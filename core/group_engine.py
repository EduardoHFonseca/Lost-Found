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


STOPWORDS_MARCA = {
    "DE", "DO", "DA", "DOS", "DAS", "E", "O", "A", "SA", "LTDA", "S", "CIA", 
    "BRASIL", "DO BRASIL", "S.A.", "S/A", "ME", "EPP", "HOLDING", "GRUPO"
}

SPORTS_EVENT_KEYWORDS = {
    "BASQUETE", "COPA", "TORNEIO", "TENIS", "NIGHT", "RUN", "CORRIDA", "MOTOCROSS", 
    "VOICE", "HACKATHON", "XPERIENCE", "NBPG", "MARATONA", "FUTEBOL", "CAMPEONATO", 
    "LSB", "BLACKSTAR", "MOURAO", "SPORT", "SHOW", "FESTIVAL", "GAMES", "ESPORTE"
}

INSTITUTIONAL_KEYWORDS = {
    "PROGRAMA", "INSTITUTO", "PROJETO", "CONTA", "LUZ", "ENERGIA", "VERDE", "REDE", 
    "RODOVIA", "SISTEMA", "DISTRIBUICAO", "GERACAO", "TRANSMISSAO", "CIMENTO", 
    "ALUMINIO", "CELULOSE", "FLORESTA", "OPERACAO", "SERVICOS", "TRANSITO", "BEM", 
    "HUMANIZADO", "SUSTENTABILIDADE", "BASTA", "JORNALISMO", "EDUCACAO", "SOCIAL"
}


KNOWN_CONGLOMERATE_TERMS = {
    "GRUPO NEOENERGIA": {
        "COELBA", "CELPE", "COSERN", "ELEKTRO", "CEB", "AFLUENTE", "BAGUARI", "ITAPEBI", 
        "TELES", "PIRES", "CAETITE", "CALANGO", "CORUMBATAI", "GOIANDIRA", "TERMOPERNAMBUCO", 
        "TERMOPE", "IBERDROLA", "FAELBA", "NARANDIBA", "DISTRITO", "VALE", "LUZ", 
        "NEOINVEST", "NEOSERV", "NEOENERGIA", "DENDRANTHEMA", "ENERGYWORKS"
    },
    "GRUPO CCR": {
        "CCR", "AUTOBAN", "DUTRA", "NOVADUTRA", "RODOANEL", "PONTE", "TIETE", "VIAOESTE", 
        "VIAQUATRO", "VIASUL", "VIALAGOS", "VIACOSTEIRA", "RODONORTE", "MSVIA", "RIOSP", 
        "METRO", "BAHIA", "AIRPORT", "VIAMOBILIDADE", "MOTIVA", "INVEPAR", "ANHANGUERA", 
        "BANDEIRANTES", "IMIGRANTES", "COSTA", "SOL"
    },
    "VOTORANTIM": {
        "VOTORANTIM", "VOTORAN", "CBA", "NEXA", "BV", "CITROSUCO", "ENGECAL", "POTY", 
        "TOCANTINS", "ITAUSA", "AUREN", "FIBRIA", "SUZANO", "ALUMINIO", "CIMENTOS"
    }
}


def evaluate_brand_coherence(
    marca: str,
    anunciante_fantasia: str,
    razao_social: Optional[str] = None,
    grupo_informado: Optional[str] = None
) -> Tuple[int, str, str]:
    """
    Avalia a coerência semântica e contextual entre Marca/Produto e o anunciante declarado.
    Retorna (score: int, categoria: str, diagnostico: str).
    """
    m_norm = normalize_text(marca)
    f_norm = normalize_text(anunciante_fantasia)
    r_norm = normalize_text(razao_social)
    g_norm = normalize_text(grupo_informado)

    if not m_norm:
        return 0, "DADOS_INCOMPLETOS", "Marca / Produto não informado"

    # Match exato de texto
    if m_norm in (f_norm, r_norm, g_norm):
        return 100, "MARCA_DIRETA", "Correspondência exata com Anunciante / Razão Social"

    m_words = set(m_norm.split()) - STOPWORDS_MARCA
    f_words = set(f_norm.split()) - STOPWORDS_MARCA
    r_words = set(r_norm.split()) - STOPWORDS_MARCA
    g_words = set(g_norm.split()) - STOPWORDS_MARCA
    corp_words = f_words | r_words | g_words

    # Termos conhecidos do conglomerado
    group_known_words = set()
    for g_key, terms in KNOWN_CONGLOMERATE_TERMS.items():
        if g_norm and (g_norm in normalize_text(g_key) or normalize_text(g_key) in g_norm):
            group_known_words = terms
            break

    shared_corp = (m_words & corp_words) | (m_words & group_known_words)
    is_sports = bool(m_words & SPORTS_EVENT_KEYWORDS)
    is_inst = bool(m_words & INSTITUTIONAL_KEYWORDS)

    if shared_corp:
        shared_str = ", ".join(sorted(list(shared_corp)))
        if is_sports:
            return 75, "PATROCINIO_CHANCELADO", f"Patrocínio / Evento com menção à marca ({shared_str})"
        elif is_inst:
            return 90, "CAMPANHA_INSTITUCIONAL", f"Ação / Linha institucional da empresa ({shared_str})"
        else:
            return 95, "MARCA_DIRETA", f"Marca / Produto vinculado ao grupo ou subsidiária ({shared_str})"

    if f_norm and (f_norm in m_norm or m_norm in f_norm):
        return 92, "MARCA_DIRETA", "Subcadeia identificada no Anunciante Fantasia"

    if r_norm and (r_norm in m_norm or m_norm in r_norm):
        return 92, "MARCA_DIRETA", "Subcadeia identificada na Razão Social"

    if is_sports:
        return 45, "PATROCINIO_ESPORTIVO", "Ação de Patrocínio Esportivo / Projeto apoiado sem marca expressa"

    if is_inst:
        return 70, "CAMPANHA_SOCIAL", "Campanha de Utilidade Pública / Slogan Institucional"

    return 35, "BAIXA_ADERENCIA", "Termo sem correlação textual ou setorial direta com o anunciante"


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
    Resolve a cadeia de relacionamento societário e consistência de marca:
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
        matched_emp = None
        for emp in conglom["empresas_conhecidas"]:
            emp_fantasia_norm = normalize_text(emp["fantasia"])
            emp_razao_norm = normalize_text(emp["razao"])

            if (norm_fantasia and (norm_fantasia == emp_fantasia_norm or norm_fantasia == emp_razao_norm)) or \
               (norm_marca and (norm_marca == emp_fantasia_norm or norm_marca == emp_razao_norm)):
                matched_emp = emp
                break

        if matched_emp:
            result["cnpj_identificado"] = matched_emp["cnpj"]
            result["cnpj_limpo"] = clean_cnpj(matched_emp["cnpj"])
            result["razao_social_identificada"] = matched_emp["razao"]
            result["eh_matriz"] = is_matriz(result["cnpj_limpo"])
            result["origem_resolucao"] = "DIRETORIO_SOCIETARIO"
        else:
            # 1.2 Match por contenção com palavras-chave completas
            for emp in conglom["empresas_conhecidas"]:
                emp_fantasia_norm = normalize_text(emp["fantasia"])
                emp_razao_norm = normalize_text(emp["razao"])

                if (norm_fantasia and len(emp_fantasia_norm) >= 4 and emp_fantasia_norm in norm_fantasia) or \
                   (norm_marca and len(emp_fantasia_norm) >= 4 and emp_fantasia_norm in norm_marca):
                    matched_emp = emp
                    break

            if matched_emp:
                result["cnpj_identificado"] = matched_emp["cnpj"]
                result["cnpj_limpo"] = clean_cnpj(matched_emp["cnpj"])
                result["razao_social_identificada"] = matched_emp["razao"]
                result["eh_matriz"] = is_matriz(result["cnpj_limpo"])
                result["origem_resolucao"] = "DIRETORIO_SOCIETARIO"
            else:
                # Holding do Grupo
                result["cnpj_identificado"] = conglom["holding_cnpj"]
                result["cnpj_limpo"] = clean_cnpj(conglom["holding_cnpj"])
                result["razao_social_identificada"] = conglom["holding_nome"]
                result["eh_matriz"] = True
                result["origem_resolucao"] = "HOLDING_DIRETORIO"

    # 2. Busca na base de Anunciantes do PostgreSQL (se db fornecido e não resolvido)
    elif db is not None:
        anunciante_match = db.query(Anunciante).filter(
            (Anunciante.anunciante_fantasia.ilike(f"%{anunciante_fantasia}%")) |
            (Anunciante.anunciante_rz_social.ilike(f"%{anunciante_fantasia}%"))
        ).first()

        if anunciante_match and anunciante_match.cnpj_formatado:
            result["cnpj_identificado"] = anunciante_match.cnpj_formatado
            result["cnpj_limpo"] = clean_cnpj(anunciante_match.cnpj_formatado)
            result["razao_social_identificada"] = anunciante_match.anunciante_rz_social or anunciante_match.razao_social_receita
            result["eh_matriz"] = anunciante_match.eh_matriz
            result["origem_resolucao"] = "BASE_ANUNCIANTES"
        else:
            result["origem_resolucao"] = "NAO_MAPEADO"
    else:
        result["origem_resolucao"] = "NAO_MAPEADO"

    # 3. Avaliação Semântica de Consistência e Coerência de Marca/Produto
    coherence_score, category, diagnostic = evaluate_brand_coherence(
        marca=marca,
        anunciante_fantasia=anunciante_fantasia,
        razao_social=result["razao_social_identificada"],
        grupo_informado=canonical_grupo or grupo_informado
    )

    result["confianca_score"] = coherence_score
    result["categoria_aderencia"] = category

    if coherence_score >= 70:
        result["status_mapeamento"] = "MAPEADO_OK"
    elif coherence_score >= 40:
        result["status_mapeamento"] = "REQUER_VALIDACAO"
    else:
        result["status_mapeamento"] = "BAIXA_ADERENCIA"

    if result["origem_resolucao"] != "NAO_MAPEADO":
        result["observacoes"] = diagnostic
    else:
        result["observacoes"] = "Empresa ou grupo não identificados automaticamente nas bases societárias."

    return result


def get_holding_360_view(db: Session, grupo_nome: Optional[str] = None, lote_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retorna a visão analítica 360° da holding consolidando:
    Grupo Econômico -> Razões Sociais / CNPJs -> Anunciantes Fantasia -> Marcas e Produtos
    """
    query = db.query(MarcaProduto)
    if lote_id:
        query = query.filter(MarcaProduto.lote_id == lote_id)
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
