import re
import random


def clean_cnpj(cnpj_input) -> str:
    """
    Remove caracteres não numéricos e ajusta zeros à esquerda para ter 14 dígitos.
    Retorna string vazia se nulo, zero ou inválido.
    """
    if cnpj_input is None:
        return ""
    
    val_str = str(cnpj_input).strip()
    if val_str in ("0", "0.0", "nan", "None", "null", ""):
        return ""

    digits_only = re.sub(r"\D", "", val_str)
    if not digits_only or set(digits_only) == {"0"}:
        return ""

    # Se tiver menos de 14 dígitos, completa com zeros à esquerda
    if len(digits_only) < 14:
        digits_only = digits_only.zfill(14)

    return digits_only


def calculate_dv(digits: str) -> int:
    """
    Calcula um dígito verificador pelo Módulo 11 oficial da Receita Federal.
    """
    if len(digits) == 12:
        weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    elif len(digits) == 13:
        weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    else:
        raise ValueError("A sequência para cálculo de DV deve ter 12 ou 13 dígitos.")

    total_sum = sum(int(d) * w for d, w in zip(digits, weights))
    remainder = total_sum % 11
    return 0 if remainder < 2 else 11 - remainder


def validate_cnpj(cnpj_input) -> tuple[bool, str, str]:
    """
    Valida um CNPJ matematicamente (tamanho 14, dígitos não repetidos, DVs corretos).
    Retorna (is_valid, cleaned_cnpj, reason).
    """
    cleaned = clean_cnpj(cnpj_input)
    if not cleaned:
        return False, "", "CNPJ ausente ou zerado"

    if len(cleaned) != 14:
        return False, cleaned, f"Tamanho inválido ({len(cleaned)} dígitos)"

    if len(set(cleaned)) == 1:
        return False, cleaned, "Sequência de dígitos idênticos"

    dv1 = calculate_dv(cleaned[:12])
    dv2 = calculate_dv(cleaned[:12] + str(dv1))

    expected_dvs = f"{dv1}{dv2}"
    actual_dvs = cleaned[12:]

    if expected_dvs != actual_dvs:
        return False, cleaned, f"Dígitos verificadores incorretos (Esperado: {expected_dvs}, Atual: {actual_dvs})"

    return True, cleaned, "CNPJ válido"


def format_cnpj(cnpj_input) -> str:
    """
    Formata um CNPJ com a máscara oficial XX.XXX.XXX/XXXX-XX.
    """
    cleaned = clean_cnpj(cnpj_input)
    if not cleaned or len(cleaned) != 14:
        return str(cnpj_input or "")

    return f"{cleaned[:2]}.{cleaned[2:5]}.{cleaned[5:8]}/{cleaned[8:12]}-{cleaned[12:]}"


def is_matriz(cnpj_input) -> bool | None:
    """
    Retorna True se o CNPJ for Matriz (/0001), False se for Filial, None se inválido.
    """
    cleaned = clean_cnpj(cnpj_input)
    if not cleaned or len(cleaned) != 14:
        return None
    return cleaned[8:12] == "0001"


def extract_cnpj_root(cnpj_input) -> str:
    """
    Retorna os 8 primeiros dígitos (CNPJ Raiz).
    """
    cleaned = clean_cnpj(cnpj_input)
    if not cleaned or len(cleaned) < 8:
        return ""
    return cleaned[:8]


def generate_cnpj(matriz: bool = True, formatted: bool = True) -> str:
    """
    Gera um CNPJ sintético válido para fins de testes.
    """
    root = "".join([str(random.randint(0, 9)) for _ in range(8)])
    branch = "0001" if matriz else f"{random.randint(2, 9999):04d}"
    base = root + branch

    dv1 = calculate_dv(base)
    dv2 = calculate_dv(base + str(dv1))
    full = base + str(dv1) + str(dv2)

    return format_cnpj(full) if formatted else full
