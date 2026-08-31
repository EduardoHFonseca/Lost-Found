import os
import sys
import unittest
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.database import SessionLocal, init_db
from database.models import LoteIngestao, Anunciante, ConsultaCNPJCache, MediacaoOperador
from core.cnpj_engine import (
    clean_cnpj,
    validate_cnpj,
    format_cnpj,
    is_matriz,
    extract_cnpj_root,
    generate_cnpj
)
from core.group_engine import (
    resolve_brand_and_group,
    get_holding_360_view,
    match_group_by_name,
    CONGLOMERADOS_CONHECIDOS
)
from services.enrichment import enrich_cnpj_info
from processors.batch_processor import process_batch_file
from processors.marca_processor import process_marca_file


class TestValidadorCNPJ(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_cnpj_cleaning_and_formatting(self):
        # CNPJ limpo e já formatado
        self.assertEqual(clean_cnpj("61.079.117/0001-05"), "61079117000105")
        self.assertEqual(format_cnpj("61079117000105"), "61.079.117/0001-05")

        # CNPJ com zeros truncados à esquerda (12 dígitos -> zfill 14)
        self.assertEqual(clean_cnpj("394544000851"), "00394544000851")
        self.assertEqual(format_cnpj("00394544000851"), "00.394.544/0008-51")

        # Nulos / Zerados
        self.assertEqual(clean_cnpj(None), "")
        self.assertEqual(clean_cnpj("0"), "")
        self.assertEqual(clean_cnpj("00000000000000"), "")

    def test_cnpj_validation_modulo11(self):
        # CNPJ Válido (Alpargatas)
        is_val, clean, reason = validate_cnpj("61.079.117/0001-05")
        self.assertTrue(is_val)
        self.assertEqual(clean, "61079117000105")

        # CNPJ Válido com Zeros à esquerda (Ministério da Saúde)
        is_val2, clean2, reason2 = validate_cnpj("394544000851")
        self.assertTrue(is_val2)
        self.assertEqual(clean2, "00394544000851")

        # CNPJ Inválido (DV errado)
        is_val3, _, _ = validate_cnpj("61079117000199")
        self.assertFalse(is_val3)

        # Sequência idêntica
        is_val4, _, _ = validate_cnpj("11111111111111")
        self.assertFalse(is_val4)

    def test_cnpj_matriz_and_generator(self):
        # Alpargatas /0001
        self.assertTrue(is_matriz("61079117000105"))
        self.assertEqual(extract_cnpj_root("61079117000105"), "61079117")

        # Filial /0035
        self.assertFalse(is_matriz("18459628003564"))

        # Gerador Sintético
        gen_matriz = generate_cnpj(matriz=True)
        is_val_gen, clean_gen, _ = validate_cnpj(gen_matriz)
        self.assertTrue(is_val_gen)
        self.assertTrue(is_matriz(clean_gen))

    def test_enrichment_cache(self):
        # Testa gravacao e leitura de cache
        cnpj_test = "61079117000105"
        res1 = enrich_cnpj_info(cnpj_test, self.db, use_network=True)
        self.assertIsNotNone(res1)
        self.assertIn(res1["origem"], ["API_EXTERNA", "CACHE_DB"])

        # Segunda chamada deve ser obrigatoriamente CACHE_DB
        res2 = enrich_cnpj_info(cnpj_test, self.db, use_network=True)
        self.assertEqual(res2["origem"], "CACHE_DB")
        self.assertEqual(res2["razao_social"], "ALPARGATAS S.A.")

    def test_batch_processor_real_csv(self):
        csv_path = "/home/efonseca/workspace/Transferencia/Lista Entrega CNPJ´s.csv"
        self.assertTrue(os.path.exists(csv_path))

        lote, objs = process_batch_file(csv_path, "Lista Entrega CNPJ´s.csv", self.db, use_network=False)
        self.assertIsNotNone(lote.id)
        self.assertEqual(lote.total_linhas, 4450)
        self.assertGreater(lote.total_validos, 3500)
        self.assertGreater(lote.total_inconsistentes, 100)
        self.assertGreater(lote.total_isentos_pf, 200)

        # Verifica presenca de conflitos de marcas compartilhando CNPJ (duplicados)
        dups = [o for o in objs if o.tipo_divergencia == "CNPJ_DUPLICADO_OUTRA_RAZAO"]
        self.assertGreater(len(dups), 0)

    def test_group_matching_and_resolution(self):
        # 1. Validação CCR
        res_ccr = resolve_brand_and_group(
            marca="AUTOBAN",
            anunciante_fantasia="AUTOBAN",
            grupo_informado="GRUPO CCR",
            db=self.db
        )
        self.assertEqual(res_ccr["status_mapeamento"], "MAPEADO_OK")
        self.assertEqual(res_ccr["cnpj_identificado"], "02.451.648/0001-44")
        self.assertTrue(res_ccr["eh_matriz"])

        # 2. Validação Neoenergia
        res_neo = resolve_brand_and_group(
            marca="AFLUENTE GERACAO",
            anunciante_fantasia="AFLUENTE",
            grupo_informado="GRUPO NEOENERGIA",
            db=self.db
        )
        self.assertEqual(res_neo["status_mapeamento"], "MAPEADO_OK")
        self.assertEqual(res_neo["cnpj_identificado"], "10.338.472/0001-20")

        # 3. Validação Votorantim
        res_vot = resolve_brand_and_group(
            marca="VOTORAN",
            anunciante_fantasia="VOTORAN",
            grupo_informado="VOTORANTIM",
            db=self.db
        )
        self.assertEqual(res_vot["status_mapeamento"], "MAPEADO_OK")
        self.assertEqual(res_vot["cnpj_identificado"], "01.637.895/0030-77")

    def test_marca_batch_processor_and_360_view(self):
        excel_path = "/home/efonseca/workspace/Validador CNPJ/data/CNPJ_2808 - Marca Fantasia.xlsx"
        self.assertTrue(os.path.exists(excel_path))

        lote, marcas_list = process_marca_file(excel_path, "CNPJ_2808 - Marca Fantasia.xlsx", self.db)
        self.assertIsNotNone(lote.id)
        self.assertEqual(lote.total_linhas, 483)
        self.assertEqual(lote.total_mapeados, 483)
        self.assertEqual(lote.total_pendentes, 0)

        # Valida View 360
        holdings = get_holding_360_view(self.db)
        self.assertGreaterEqual(len(holdings), 3)

        nomes_grupos = [h["grupo_nome"] for h in holdings]
        self.assertIn("GRUPO CCR", nomes_grupos)
        self.assertIn("GRUPO NEOENERGIA", nomes_grupos)
        self.assertIn("VOTORANTIM", nomes_grupos)


if __name__ == "__main__":
    unittest.main()
