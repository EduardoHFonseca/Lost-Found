import os
import pandas as pd
from typing import Tuple, List, Dict
from sqlalchemy.orm import Session
from database.models import LoteIngestao, Anunciante
from core.cnpj_engine import clean_cnpj, validate_cnpj, format_cnpj, is_matriz, extract_cnpj_root
from services.enrichment import enrich_cnpj_info


def process_batch_file(
    file_path_or_buffer,
    filename: str,
    db: Session,
    use_network: bool = False,
    progress_callback=None
) -> Tuple[LoteIngestao, List[Dict]]:
    """
    Carrega um arquivo CSV ou Excel, processa as validações de CNPJ, verifica
    conflitos entre anunciantes/razões sociais e persiste tudo no PostgreSQL.
    """
    # 1. Leitura do arquivo (CSV ou XLSX)
    if isinstance(file_path_or_buffer, str):
        filename = os.path.basename(file_path_or_buffer)
        if file_path_or_buffer.endswith(".xlsx") or file_path_or_buffer.endswith(".xls"):
            df = pd.read_excel(file_path_or_buffer)
        else:
            df = pd.read_csv(file_path_or_buffer, encoding="utf-8-sig", sep=None, engine="python")
    else:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(file_path_or_buffer)
        else:
            df = pd.read_csv(file_path_or_buffer, encoding="utf-8-sig", sep=None, engine="python")

    # Mapeamento e normalização de colunas
    col_mapping = {
        "Cod Anunciante Razão": "cod_anunciante_razao",
        "Anunciante Rz Social": "anunciante_rz_social",
        "CNPJ": "cnpj_original",
        "Cod Anunc Fantasia": "cod_anunc_fantasia",
        "Anunciante Fantasia": "anunciante_fantasia"
    }
    
    # Renomeia colunas se baterem com o padrão do CSV enviado
    df = df.rename(columns={c: col_mapping[c] for c in df.columns if c in col_mapping})

    # Garante que colunas esperadas existam
    for req_col in ["cod_anunciante_razao", "anunciante_rz_social", "cnpj_original", "cod_anunc_fantasia", "anunciante_fantasia"]:
        if req_col not in df.columns:
            df[req_col] = None

    total_rows = len(df)

    # 2. Registra Lote de Ingestão
    lote = LoteIngestao(
        nome_arquivo=filename,
        total_linhas=total_rows,
        status_lote="PROCESSANDO"
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)

    anunciantes_objetos = []
    
    # 3. Primeira passagem: Sanitização, validação e enriquecimento individual
    for idx, row in df.iterrows():
        if progress_callback and total_rows > 0:
            progress_callback(int((idx / total_rows) * 50)) # Primeiros 50%

        cod_rz = str(row["cod_anunciante_razao"]).strip() if pd.notna(row["cod_anunciante_razao"]) else ""
        rz_social = str(row["anunciante_rz_social"]).strip() if pd.notna(row["anunciante_rz_social"]) else ""
        cnpj_raw = str(row["cnpj_original"]).strip() if pd.notna(row["cnpj_original"]) else ""
        cod_fant = str(row["cod_anunc_fantasia"]).strip() if pd.notna(row["cod_anunc_fantasia"]) else ""
        fantasia = str(row["anunciante_fantasia"]).strip() if pd.notna(row["anunciante_fantasia"]) else ""

        is_valid, cleaned, reason = validate_cnpj(cnpj_raw)

        if not cleaned:
            status_val = "ISENTO_PF"
            tipo_div = "SEM_CNPJ"
            fmt_cnpj = ""
            matriz_flag = None
            matriz_sug = None
            sit_cadastral = "ISENTO_PF"
            rz_receita = None
            fant_receita = None
            cnae = None
            uf = None
        elif not is_valid:
            status_val = "REQUER_MEDIACAO"
            tipo_div = "CNPJ_INVALIDO_DV"
            fmt_cnpj = format_cnpj(cleaned)
            matriz_flag = is_matriz(cleaned)
            root = extract_cnpj_root(cleaned)
            matriz_sug = format_cnpj(f"{root}0001") if root else None
            sit_cadastral = "INVALIDO"
            rz_receita = None
            fant_receita = None
            cnae = None
            uf = None
        else:
            fmt_cnpj = format_cnpj(cleaned)
            matriz_flag = is_matriz(cleaned)
            root = extract_cnpj_root(cleaned)
            matriz_sug = format_cnpj(f"{root}0001") if root else None

            # Enriquecimento (Cache DB ou API)
            info = enrich_cnpj_info(cleaned, db, use_network=use_network)

            sit_cadastral = info.get("situacao_cadastral", "ATIVA")
            rz_receita = info.get("razao_social")
            fant_receita = info.get("nome_fantasia")
            cnae = info.get("cnae_principal")
            uf = info.get("uf")

            if sit_cadastral in ["INATIVA", "BAIXADA", "SUSPENSA", "INAPTA"]:
                status_val = "REQUER_MEDIACAO"
                tipo_div = "CNPJ_INATIVO"
            elif not matriz_flag:
                status_val = "REQUER_MEDIACAO"
                tipo_div = "FILIAL_EM_RAIZ"
            else:
                status_val = "VALIDO_OK"
                tipo_div = None

        anu = Anunciante(
            lote_id=lote.id,
            cod_anunciante_razao=cod_rz,
            anunciante_rz_social=rz_social,
            cnpj_original=cnpj_raw,
            cod_anunc_fantasia=cod_fant,
            anunciante_fantasia=fantasia,
            cnpj_limpo=cleaned,
            cnpj_formatado=fmt_cnpj,
            eh_matriz=matriz_flag,
            cnpj_matriz_sugerido=matriz_sug,
            situacao_cadastral=sit_cadastral,
            razao_social_receita=rz_receita,
            nome_fantasia_receita=fant_receita,
            cnae_principal=cnae,
            uf=uf,
            status_validacao=status_val,
            tipo_divergencia=tipo_div
        )
        anunciantes_objetos.append(anu)

    # 4. Segunda passagem: Identificação de conflitos cruzados (CNPJ duplicado em anunciantes/marcas diferentes)
    cnpj_map: Dict[str, List[Anunciante]] = {}
    for a in anunciantes_objetos:
        if a.cnpj_limpo:
            cnpj_map.setdefault(a.cnpj_limpo, []).append(a)

    for cleaned_cnpj, obj_list in cnpj_map.items():
        if len(obj_list) > 1:
            # Verifica se pertencem a razões sociais ou nomes fantasias distintos
            distinct_codes = {o.cod_anunciante_razao for o in obj_list if o.cod_anunciante_razao}
            distinct_fantasias = {o.anunciante_fantasia.lower() for o in obj_list if o.anunciante_fantasia}
            
            if len(distinct_codes) > 1 or len(distinct_fantasias) > 1:
                # Caso clássico do McDonald's vs Arcos Dourados compartilhando o mesmo CNPJ!
                for o in obj_list:
                    o.status_validacao = "REQUER_MEDIACAO"
                    o.tipo_divergencia = "CNPJ_DUPLICADO_OUTRA_RAZAO"

    # Persiste todos os registros no PostgreSQL
    db.add_all(anunciantes_objetos)
    db.commit()

    # 5. Atualiza totais do Lote
    cnt_validos = sum(1 for a in anunciantes_objetos if a.status_validacao == "VALIDO_OK")
    cnt_inconsistentes = sum(1 for a in anunciantes_objetos if a.status_validacao == "REQUER_MEDIACAO")
    cnt_isentos = sum(1 for a in anunciantes_objetos if a.status_validacao == "ISENTO_PF")

    lote.total_validos = cnt_validos
    lote.total_inconsistentes = cnt_inconsistentes
    lote.total_isentos_pf = cnt_isentos
    lote.status_lote = "EM_MEDIACAO" if cnt_inconsistentes > 0 else "CONCLUIDO"

    db.commit()
    db.refresh(lote)

    if progress_callback:
        progress_callback(100)

    return lote, anunciantes_objetos
