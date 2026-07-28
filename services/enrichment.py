import time
import requests
from sqlalchemy.orm import Session
from database.models import ConsultaCNPJCache
from core.cnpj_engine import clean_cnpj, is_matriz, extract_cnpj_root, format_cnpj


BRASIL_API_URL = "https://brasilapi.com.br/api/cnpj/v1/{}"
RECEITA_WS_URL = "https://receitaws.com.br/v1/cnpj/{}"


def enrich_cnpj_info(cnpj_input: str, db: Session, use_network: bool = True) -> dict:
    """
    Enriquece informações de um CNPJ utilizando cache no PostgreSQL e APIs públicas.
    Retorna um dicionário padronizado com dados cadastrais.
    """
    cleaned = clean_cnpj(cnpj_input)
    if not cleaned or len(cleaned) != 14:
        return {
            "cnpj_limpo": cleaned,
            "situacao_cadastral": "ISENTO_PF" if not cleaned else "INVALIDO",
            "razao_social": None,
            "nome_fantasia": None,
            "cnae_principal": None,
            "uf": None,
            "eh_matriz": None,
            "cnpj_matriz": None,
            "origem": "VALIDACAO_LOCAL"
        }

    # 1. Verifica no Cache do PostgreSQL
    cache_entry = db.query(ConsultaCNPJCache).filter(ConsultaCNPJCache.cnpj_limpo == cleaned).first()
    if cache_entry:
        return {
            "cnpj_limpo": cache_entry.cnpj_limpo,
            "situacao_cadastral": cache_entry.situacao_cadastral or "ATIVA",
            "razao_social": cache_entry.razao_social,
            "nome_fantasia": cache_entry.nome_fantasia,
            "cnae_principal": cache_entry.dados_json.get("cnae_fiscal_descricao") if isinstance(cache_entry.dados_json, dict) else None,
            "uf": cache_entry.dados_json.get("uf") if isinstance(cache_entry.dados_json, dict) else None,
            "eh_matriz": cache_entry.eh_matriz,
            "cnpj_matriz": cache_entry.cnpj_matriz,
            "origem": "CACHE_DB"
        }

    if not use_network:
        # Fallback offline sem rede
        matriz_flag = is_matriz(cleaned)
        root = extract_cnpj_root(cleaned)
        matriz_cnpj = f"{root}0001" + "00" if root else None
        return {
            "cnpj_limpo": cleaned,
            "situacao_cadastral": "ATIVA", # Assumido por padrão offline
            "razao_social": None,
            "nome_fantasia": None,
            "cnae_principal": None,
            "uf": None,
            "eh_matriz": matriz_flag,
            "cnpj_matriz": matriz_cnpj,
            "origem": "OFFLINE_RULE"
        }

    # 2. Tenta Consulta na BrasilAPI
    res_data = None
    try:
        url = BRASIL_API_URL.format(cleaned)
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            res_data = resp.json()
    except Exception:
        pass

    # 3. Fallback ReceitaWS
    if not res_data:
        try:
            url = RECEITA_WS_URL.format(cleaned)
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                raw_data = resp.json()
                if raw_data.get("status") != "ERROR":
                    res_data = {
                        "descricao_situacao_cadastral": raw_data.get("situacao"),
                        "razao_social": raw_data.get("nome"),
                        "nome_fantasia": raw_data.get("fantasia"),
                        "cnae_fiscal_descricao": raw_data.get("atividade_principal", [{}])[0].get("text"),
                        "uf": raw_data.get("uf"),
                        "identificador_matriz_filial": 1 if raw_data.get("tipo") == "MATRIZ" else 2
                    }
        except Exception:
            pass

    # 4. Trata e Armazena no Cache do PostgreSQL
    matriz_flag = is_matriz(cleaned)
    root = extract_cnpj_root(cleaned)
    cnpj_matriz_sugerido = f"{root}0001" if root else None

    if res_data:
        situacao = str(res_data.get("descricao_situacao_cadastral") or "ATIVA").upper()
        razao = res_data.get("razao_social") or res_data.get("nome")
        fantasia = res_data.get("nome_fantasia") or res_data.get("fantasia")
        cnae = res_data.get("cnae_fiscal_descricao")
        uf = res_data.get("uf")
        
        # Salva no DB Cache
        new_cache = ConsultaCNPJCache(
            cnpj_limpo=cleaned,
            dados_json=res_data,
            situacao_cadastral=situacao,
            eh_matriz=matriz_flag,
            cnpj_matriz=cnpj_matriz_sugerido,
            razao_social=razao,
            nome_fantasia=fantasia
        )
        db.merge(new_cache)
        try:
            db.commit()
        except Exception:
            db.rollback()

        return {
            "cnpj_limpo": cleaned,
            "situacao_cadastral": situacao,
            "razao_social": razao,
            "nome_fantasia": fantasia,
            "cnae_principal": cnae,
            "uf": uf,
            "eh_matriz": matriz_flag,
            "cnpj_matriz": cnpj_matriz_sugerido,
            "origem": "API_EXTERNA"
        }
    else:
        # Registra no cache como não encontrado para não poluir chamadas repetidas
        fallback_cache = ConsultaCNPJCache(
            cnpj_limpo=cleaned,
            dados_json={"status": "nao_encontrado"},
            situacao_cadastral="DESCONHECIDO",
            eh_matriz=matriz_flag,
            cnpj_matriz=cnpj_matriz_sugerido,
            razao_social=None,
            nome_fantasia=None
        )
        db.merge(fallback_cache)
        try:
            db.commit()
        except Exception:
            db.rollback()

        return {
            "cnpj_limpo": cleaned,
            "situacao_cadastral": "DESCONHECIDO",
            "razao_social": None,
            "nome_fantasia": None,
            "cnae_principal": None,
            "uf": None,
            "eh_matriz": matriz_flag,
            "cnpj_matriz": cnpj_matriz_sugerido,
            "origem": "OFFLINE_FALLBACK"
        }
