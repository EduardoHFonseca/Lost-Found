import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from core.cnpj_engine import clean_cnpj, format_cnpj, is_matriz, extract_cnpj_root
from database.models import Anunciante, ConsultaCNPJCache, GrupoEconomico, MarcaProduto


def normalize_text(text: Optional[str]) -> str:
    """Normaliza texto removendo acentos, pontuação e espaços extras."""
    if not text:
        return ""
    # Remove acentos
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    # Converte para maiúsculas e remove caracteres especiais desnecessários
    text = re.sub(r"[^\w\s]", " ", text.upper())
    # Remove espaços duplos
    return re.sub(r"\s+", " ", text).strip()


# Diretório de Conhecimento Societário dos Principais Conglomerados
CONGLOMERADOS_CONHECIDOS = {
    "GRUPO CCR": {
        "holding_nome": "CCR S.A.",
        "holding_cnpj": "02.846.056/0001-97",
        "aliases_grupo": ["CCR", "GRUPO CCR", "COMPANHIA DE CONCESSOES RODOVIARIAS"],
        "empresas_conhecidas": [
            {"razao": "CCR S.A.", "cnpj": "02.846.056/0001-97", "fantasia": "CCR"},
            {"razao": "CONCESSIONARIA DO SISTEMA ANHANGUERA-BANDEIRANTES S.A.", "cnpj": "02.451.648/0001-44", "fantasia": "AUTOBAN"},
            {"razao": "CONCESSIONARIA DA RODOVIA PRESIDENTE DUTRA S.A.", "cnpj": "00.999.645/0001-08", "fantasia": "NOVA DUTRA"},
            {"razao": "CONCESSIONARIA DO RODOANEL OESTE S.A.", "cnpj": "09.525.688/0001-52", "fantasia": "RODOANEL"},
            {"razao": "CONCESSIONARIA DA PONTE RIO-NITEROI S.A.", "cnpj": "00.567.890/0001-32", "fantasia": "PONTE"},
            {"razao": "CONCESSIONARIA RODOVIAS DO TIETE S.A.", "cnpj": "10.874.198/0001-92", "fantasia": "RODOVIAS DO TIETE"},
            {"razao": "CONCESSIONARIA RODOVIAS INTEGRADAS DO OESTE S.A.", "cnpj": "02.846.123/0001-40", "fantasia": "VIAOESTE"},
            {"razao": "CONCESSIONARIA DA LINHA 4 DO METRO DE SAO PAULO S.A.", "cnpj": "08.487.654/0001-21", "fantasia": "VIAQUATRO"},
        ]
    },
    "GRUPO NEOENERGIA": {
        "holding_nome": "NEOENERGIA S.A.",
        "holding_cnpj": "01.083.200/0001-18",
        "aliases_grupo": ["NEOENERGIA", "GRUPO NEOENERGIA", "IBERDROLA BRASIL"],
        "empresas_conhecidas": [
            {"razao": "NEOENERGIA S.A.", "cnpj": "01.083.200/0001-18", "fantasia": "NEOENERGIA"},
            {"razao": "COMPANHIA DE ELETRICIDADE DO ESTADO DA BAHIA COELBA", "cnpj": "15.139.629/0001-94", "fantasia": "NEOENERGIA COELBA"},
            {"razao": "COMPANHIA ENERGETICA DE PERNAMBUCO CELPE", "cnpj": "10.835.932/0001-08", "fantasia": "NEOENERGIA PERNAMBUCO"},
            {"razao": "COMPANHIA ENERGETICA DO RIO GRANDE DO NORTE COSERN", "cnpj": "08.324.196/0001-81", "fantasia": "NEOENERGIA COSERN"},
            {"razao": "ELEKTRO REDES S.A.", "cnpj": "02.328.280/0001-97", "fantasia": "NEOENERGIA ELEKTRO"},
            {"razao": "NEOENERGIA DISTRIBUICAO BRASILIA S.A.", "cnpj": "00.070.723/0001-08", "fantasia": "NEOENERGIA BRASILIA"},
            {"razao": "AFLUENTE TRANSMISSAO DE ENERGIA ELETRICA S.A.", "cnpj": "10.338.472/0001-20", "fantasia": "AFLUENTE"},
            {"razao": "BAGUARI I GERACAO DE ENERGIA S.A.", "cnpj": "08.647.930/0001-80", "fantasia": "BAGUARI"},
            {"razao": "BAHIA PCH I ENERGIA S.A.", "cnpj": "07.839.201/0001-44", "fantasia": "BAHIA PCH I"},
            {"razao": "BAHIA PCH II ENERGIA S.A.", "cnpj": "07.839.202/0001-99", "fantasia": "BAHIA PCH II"},
            {"razao": "NORTE ENERGIA S.A. (BELO MONTE)", "cnpj": "12.300.288/0001-07", "fantasia": "BELO MONTE PARTICIPACOES"},
            {"razao": "CAETITE 1 ENERGIA RENOVAVEL S.A.", "cnpj": "14.289.442/0001-33", "fantasia": "CAETITE 1 ENERGIA RENOVAVEL"},
            {"razao": "CAETITE 2 ENERGIA RENOVAVEL S.A.", "cnpj": "14.289.450/0001-80", "fantasia": "CAETITE 2 ENERGIA RENOVAVEL"},
            {"razao": "CAETITE 3 ENERGIA RENOVAVEL S.A.", "cnpj": "14.289.460/0001-15", "fantasia": "CAETITE 3 ENERGIA RENOVAVEL"},
            {"razao": "CALANGO 1 ENERGIA RENOVAVEL S.A.", "cnpj": "14.290.111/0001-60", "fantasia": "CALANGO 1 ENERGIA RENOVAVEL"},
            {"razao": "CORUMBATAI GERACAO S.A.", "cnpj": "06.128.455/0001-20", "fantasia": "CORUMBATAI"},
            {"razao": "GOIANDIRA GERACAO DE ENERGIA S.A.", "cnpj": "05.890.123/0001-45", "fantasia": "GOIANDIRA"},
        ]
    },
    "VOTORANTIM": {
        "holding_nome": "VOTORANTIM S.A.",
        "holding_cnpj": "03.407.049/0001-51",
        "aliases_grupo": ["VOTORANTIM", "GRUPO VOTORANTIM", "HEJOASSU"],
        "empresas_conhecidas": [
            {"razao": "VOTORANTIM S.A.", "cnpj": "03.407.049/0001-51", "fantasia": "VOTORANTIM"},
            {"razao": "VOTORANTIM CIMENTOS S.A.", "cnpj": "01.637.895/0001-32", "fantasia": "VOTORANTIM CIMENTOS"},
            {"razao": "COMPANHIA BRASILEIRA DE ALUMINIO (CBA)", "cnpj": "61.409.892/0001-73", "fantasia": "CBA"},
            {"razao": "NEXA RECURSOS MINERAIS S.A.", "cnpj": "43.746.119/0001-12", "fantasia": "NEXA / VOTORANTIM METAIS"},
            {"razao": "BANCO VOTORANTIM S.A.", "cnpj": "59.588.111/0001-03", "fantasia": "BANCO BV"},
            {"razao": "CITROSUCO S.A. AGROINDUSTRIA", "cnpj": "03.953.535/0001-30", "fantasia": "CITROSUCO"},
            {"razao": "ENGECAL ENGENHARIA E CALCARIO LTDA", "cnpj": "01.637.895/0045-53", "fantasia": "ENGECAL"},
            {"razao": "CIMENTO POTY LTDA", "cnpj": "01.637.895/0010-23", "fantasia": "POTY"},
            {"razao": "CIMENTO TOCANTINS S.A.", "cnpj": "01.637.895/0020-03", "fantasia": "TOCANTINS"},
            {"razao": "CIMENTO VOTORAN S.A.", "cnpj": "01.637.895/0030-77", "fantasia": "VOTORAN"},
            {"razao": "CIMENTO ITAUSA S.A.", "cnpj": "01.637.895/0040-49", "fantasia": "ITAUSA"},
            {"razao": "VOTORANTIM ENERGIA LTDA", "cnpj": "04.567.890/0001-12", "fantasia": "VOTORANTIM ENERGIA"},
        ]
    }
}


def match_group_by_name(grupo_str: Optional[str]) -> Optional[str]:
    """Retorna a chave canônica do grupo a partir do nome ou sinônimos informados."""
    if not grupo_str:
        return None
    norm = normalize_text(grupo_str)
    for canonical_name, data in CONGLOMERADOS_CONHECIDOS.items():
        if norm == normalize_text(canonical_name):
            return canonical_name
        for alias in data["aliases_grupo"]:
            if norm == normalize_text(alias) or alias in norm:
                return canonical_name
    return None


def resolve_brand_and_group(
    marca: str,
    anunciante_fantasia: str,
    grupo_informado: str,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Resolve a cadeia de relacionamento societário:
    Marca/Produto -> Anunciante Fantasia -> Razão Social -> CNPJ -> Grupo Econômico
    """
    norm_marca = normalize_text(marca)
    norm_fantasia = normalize_text(anunciante_fantasia)
    norm_grupo = normalize_text(grupo_informado)

    canonical_grupo = match_group_by_name(grupo_informado)

    result = {
        "marca": marca,
        "anunciante_fantasia": anunciante_fantasia,
        "grupo_informado": grupo_informado,
        "grupo_canonico": canonical_grupo or grupo_informado,
        "cnpj_identificado": None,
        "cnpj_limpo": None,
        "razao_social_identificada": None,
        "eh_matriz": None,
        "pertence_grupo": True,
        "confianca_score": 0,
        "status_mapeamento": "REQUER_VALIDACAO",
        "origem_resolucao": None,
        "observacoes": None
    }

    # 1. Busca no Diretório de Conglomerados Conhecidos
    if canonical_grupo and canonical_grupo in CONGLOMERADOS_CONHECIDOS:
        conglom = CONGLOMERADOS_CONHECIDOS[canonical_grupo]
        
        # 1.1 Match exato prioritário por nome fantasia ou razão social
        for emp in conglom["empresas_conhecidas"]:
            emp_fantasia_norm = normalize_text(emp["fantasia"])
            emp_razao_norm = normalize_text(emp["razao"])

            if (norm_fantasia and (norm_fantasia == emp_fantasia_norm or norm_fantasia == emp_razao_norm)) or \
               (norm_marca and (norm_marca == emp_fantasia_norm or norm_marca == emp_razao_norm)):
                result["cnpj_identificado"] = emp["cnpj"]
                result["cnpj_limpo"] = clean_cnpj(emp["cnpj"])
                result["razao_social_identificada"] = emp["razao"]
                result["eh_matriz"] = is_matriz(result["cnpj_limpo"])
                result["confianca_score"] = 98
                result["status_mapeamento"] = "MAPEADO_OK"
                result["origem_resolucao"] = "DIRETORIO_SOCIETARIO"
                result["observacoes"] = f"Vinculado à subsidiária '{emp['razao']}' do conglomerado {canonical_grupo}."
                return result

        # 1.2 Match por contenção com palavras-chave completas
        for emp in conglom["empresas_conhecidas"]:
            emp_fantasia_norm = normalize_text(emp["fantasia"])
            emp_razao_norm = normalize_text(emp["razao"])

            # Valida se o termo é substring significativa (tamanho >= 4) e presente como palavra
            if (norm_fantasia and len(emp_fantasia_norm) >= 4 and emp_fantasia_norm in norm_fantasia) or \
               (norm_marca and len(emp_fantasia_norm) >= 4 and emp_fantasia_norm in norm_marca):
                result["cnpj_identificado"] = emp["cnpj"]
                result["cnpj_limpo"] = clean_cnpj(emp["cnpj"])
                result["razao_social_identificada"] = emp["razao"]
                result["eh_matriz"] = is_matriz(result["cnpj_limpo"])
                result["confianca_score"] = 92
                result["status_mapeamento"] = "MAPEADO_OK"
                result["origem_resolucao"] = "DIRETORIO_SOCIETARIO"
                result["observacoes"] = f"Vinculado à subsidiária '{emp['razao']}' do conglomerado {canonical_grupo}."
                return result

        # Se não achou empresa específica do grupo, vincula à Holding do Grupo
        result["cnpj_identificado"] = conglom["holding_cnpj"]
        result["cnpj_limpo"] = clean_cnpj(conglom["holding_cnpj"])
        result["razao_social_identificada"] = conglom["holding_nome"]
        result["eh_matriz"] = True
        result["confianca_score"] = 85
        result["status_mapeamento"] = "MAPEADO_OK"
        result["origem_resolucao"] = "HOLDING_DIRETORIO"
        result["observacoes"] = f"Vinculado à Holding controladora '{conglom['holding_nome']}' ({conglom['holding_cnpj']})."
        return result

    # 2. Busca na base de Anunciantes do PostgreSQL (se db fornecido)
    if db is not None:
        # Busca exata ou por similaridade na tabela anunciantes
        anunciante_match = db.query(Anunciante).filter(
            (Anunciante.anunciante_fantasia.ilike(f"%{anunciante_fantasia}%")) |
            (Anunciante.anunciante_rz_social.ilike(f"%{anunciante_fantasia}%"))
        ).first()

        if anunciante_match and anunciante_match.cnpj_formatado:
            result["cnpj_identificado"] = anunciante_match.cnpj_formatado
            result["cnpj_limpo"] = anunciante_match.cnpj_limpo
            result["razao_social_identificada"] = anunciante_match.anunciante_rz_social or anunciante_match.razao_social_receita
            result["eh_matriz"] = anunciante_match.eh_matriz
            result["confianca_score"] = 90
            result["status_mapeamento"] = "MAPEADO_OK"
            result["origem_resolucao"] = "BASE_ANUNCIANTES"
            result["observacoes"] = f"Localizado na base de anunciantes históricos do banco."
            return result

    # Se não foi possível mapear com alta certeza
    result["status_mapeamento"] = "REQUER_VALIDACAO"
    result["confianca_score"] = 30
    result["origem_resolucao"] = "NAO_MAPEADO"
    result["observacoes"] = "Empresa ou grupo não identificados automaticamente nas bases societárias."
    return result


def get_holding_360_view(db: Session, grupo_nome: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retorna a visão analítica 360° da holding consolidando:
    Grupo Econômico -> Razões Sociais / CNPJs -> Anunciantes Fantasia -> Marcas e Produtos
    """
    query = db.query(MarcaProduto)
    if grupo_nome:
        query = query.filter(MarcaProduto.grupo_informado.ilike(f"%{grupo_nome}%"))
    
    marcas = query.all()
    
    # Agrupa por Grupo e CNPJ/Razão Social
    grupos_dict: Dict[str, Dict[str, Any]] = {}

    for m in marcas:
        grp = m.grupo_informado or "OUTROS"
        if grp not in grupos_dict:
            grupos_dict[grp] = {
                "grupo_nome": grp,
                "total_marcas": 0,
                "total_anunciantes_fantasia": set(),
                "cnpjs_associados": set(),
                "razoes_sociais": set(),
                "empresas": {}
            }
        
        g_entry = grupos_dict[grp]
        g_entry["total_marcas"] += 1
        g_entry["total_anunciantes_fantasia"].add(m.anunciante_fantasia)
        if m.cnpj_identificado:
            g_entry["cnpjs_associados"].add(m.cnpj_identificado)
        if m.razao_social_identificada:
            g_entry["razoes_sociais"].add(m.razao_social_identificada)

        emp_key = m.razao_social_identificada or m.anunciante_fantasia
        if emp_key not in g_entry["empresas"]:
            g_entry["empresas"][emp_key] = {
                "razao_social": m.razao_social_identificada or "A Definir",
                "cnpj": m.cnpj_identificado or "Pendente",
                "anunciante_fantasia": m.anunciante_fantasia,
                "eh_matriz": m.eh_matriz,
                "marcas": []
            }
        
        if m.marca not in g_entry["empresas"][emp_key]["marcas"]:
            g_entry["empresas"][emp_key]["marcas"].append(m.marca)

    # Converte sets em listas e totais formatados
    result_list = []
    for grp, data in grupos_dict.items():
        result_list.append({
            "grupo_nome": data["grupo_nome"],
            "total_marcas": data["total_marcas"],
            "total_anunciantes": len(data["total_anunciantes_fantasia"]),
            "total_cnpjs": len(data["cnpjs_associados"]),
            "cnpjs": list(data["cnpjs_associados"]),
            "razoes_sociais": list(data["razoes_sociais"]),
            "empresas_detalhadas": list(data["empresas"].values())
        })

    return result_list
