import os
import io
import pandas as pd
from typing import Tuple, List, Dict, Optional
from sqlalchemy.orm import Session

from database.models import LoteMarca, MarcaProduto, GrupoEconomico
from core.group_engine import resolve_brand_and_group, CONGLOMERADOS_CONHECIDOS


def process_marca_file(
    file_path_or_buffer,
    filename: str,
    db: Session,
    progress_callback=None
) -> Tuple[LoteMarca, List[MarcaProduto]]:
    """
    Processa arquivo de marcas/produtos x anunciante fantasia x grupo econômico,
    resolve a linhagem societária de CNPJ/Razão Social e persiste no PostgreSQL.
    """
    # 1. Carrega dados
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

    # Mapeamento flexível de colunas
    col_mapping = {
        "Marca": "marca",
        "MARCA": "marca",
        "Anunc Fantasia": "anunciante_fantasia",
        "Anunciante Fantasia": "anunciante_fantasia",
        "ANUNC FANTASIA": "anunciante_fantasia",
        "Grupo Anunciante": "grupo_informado",
        "Grupo Economico": "grupo_informado",
        "Grupo Econômico": "grupo_informado",
        "GRUPO ANUNCIANTE": "grupo_informado"
    }

    df = df.rename(columns={c: col_mapping[c] for c in df.columns if c in col_mapping})

    for req in ["marca", "anunciante_fantasia", "grupo_informado"]:
        if req not in df.columns:
            df[req] = ""

    total_rows = len(df)

    # 2. Inicializa ou sincroniza Grupos Econômicos conhecidos na tabela grupos_economicos
    for grp_name, grp_data in CONGLOMERADOS_CONHECIDOS.items():
        existing_grp = db.query(GrupoEconomico).filter(GrupoEconomico.nome_grupo == grp_name).first()
        if not existing_grp:
            new_grp = GrupoEconomico(
                nome_grupo=grp_name,
                cnpj_holding=grp_data["holding_cnpj"],
                descricao=f"Holding controladora: {grp_data['holding_nome']}"
            )
            db.add(new_grp)
    db.commit()

    # 3. Registra Lote de Marca
    lote = LoteMarca(
        nome_arquivo=filename,
        total_linhas=total_rows,
        status_lote="PROCESSANDO"
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)

    marcas_objetos = []
    
    # 4. Processamento individual de cada registro
    for idx, row in df.iterrows():
        if progress_callback and total_rows > 0:
            progress_callback(int((idx / total_rows) * 100))

        marca_val = str(row["marca"]).strip() if pd.notna(row["marca"]) else ""
        fantasia_val = str(row["anunciante_fantasia"]).strip() if pd.notna(row["anunciante_fantasia"]) else ""
        grupo_val = str(row["grupo_informado"]).strip() if pd.notna(row["grupo_informado"]) else ""

        resolved = resolve_brand_and_group(
            marca=marca_val,
            anunciante_fantasia=fantasia_val,
            grupo_informado=grupo_val,
            db=db
        )

        # Encontra ID do Grupo no banco
        grupo_obj = db.query(GrupoEconomico).filter(GrupoEconomico.nome_grupo == resolved["grupo_canonico"]).first()
        grupo_id = grupo_obj.id if grupo_obj else None

        obj = MarcaProduto(
            lote_id=lote.id,
            grupo_id=grupo_id,
            marca=marca_val,
            anunciante_fantasia=fantasia_val,
            grupo_informado=grupo_val,
            cnpj_identificado=resolved["cnpj_identificado"],
            cnpj_limpo=resolved["cnpj_limpo"],
            razao_social_identificada=resolved["razao_social_identificada"],
            eh_matriz=resolved["eh_matriz"],
            pertence_grupo=resolved["pertence_grupo"],
            confianca_score=resolved["confianca_score"],
            status_mapeamento=resolved["status_mapeamento"],
            origem_resolucao=resolved["origem_resolucao"],
            observacoes=resolved["observacoes"]
        )
        marcas_objetos.append(obj)

    # 5. Persiste registros
    db.add_all(marcas_objetos)
    db.commit()

    # 6. Atualiza totais do Lote
    mapeados = sum(1 for m in marcas_objetos if m.status_mapeamento == "MAPEADO_OK")
    pendentes = sum(1 for m in marcas_objetos if m.status_mapeamento != "MAPEADO_OK")

    lote.total_mapeados = mapeados
    lote.total_pendentes = pendentes
    lote.status_lote = "CONCLUIDO"
    db.commit()
    db.refresh(lote)

    if progress_callback:
        progress_callback(100)

    return lote, marcas_objetos
