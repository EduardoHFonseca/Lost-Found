import datetime
from database import engine, Base, SessionLocal
from models import Channel, Programme, SpotDifference, KpiMetric

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Channels
        channels_data = [
            {"code": "TV_GLOBO", "name": "TV Globo", "media_type": "TV", "region": "São Paulo"},
            {"code": "RECORD_TV", "name": "Record TV", "media_type": "TV", "region": "São Paulo"},
            {"code": "SBT", "name": "SBT", "media_type": "TV", "region": "São Paulo"},
            {"code": "BAND", "name": "Band", "media_type": "TV", "region": "São Paulo"},
            {"code": "RADIO_CBN", "name": "Rádio CBN FM", "media_type": "Radio", "region": "São Paulo"},
            {"code": "GLOBO_ONLINE", "name": "G1 / Globoplay", "media_type": "Online", "region": "Nacional"},
        ]
        
        channels = []
        for c in channels_data:
            channel = Channel(**c)
            db.add(channel)
            channels.append(channel)
        db.commit()

        today = datetime.date.today()
        deadline_time = datetime.datetime.now() + datetime.timedelta(hours=18)

        # 2. Programmes (Novos Programas e Divergências de Grade)
        programmes_data = [
            # Novos Programas
            {
                "channel_code": "TV_GLOBO",
                "broadcast_date": today,
                "start_time": "14:15",
                "end_time": "15:30",
                "original_title": "ESPECIAL OLIMPIADAS PARIS 2026",
                "subtitle": "Bastidores e Preparativos",
                "harmonized_title": "ESPECIAL OLIMPIADAS 2026",
                "proposed_harmonized_title": "ESPECIAL ESPORTE OLIMPICO",
                "category": "Esportes",
                "proposed_category": "Jornalismo Esportivo",
                "repeat_code": "N",
                "reconciliation_key": "GLO_20260731_1415",
                "programme_before_title": "SESSÃO DA TARDE",
                "mismatch_type": "Novo Conteúdo / Subtituição",
                "is_new_programme": 1,
                "status": "New",
                "delivery_cycle": "Initial Delivery",
                "feedback_comments": "Aguardando aprovação da emissora para novo título harmonizado.",
                "deadline": deadline_time
            },
            {
                "channel_code": "RECORD_TV",
                "broadcast_date": today,
                "start_time": "22:45",
                "end_time": "23:45",
                "original_title": "DOC RECORD - INVESTIGAÇÕES ESPECIAIS",
                "subtitle": "Episódio Inédito",
                "harmonized_title": "DOC RECORD",
                "proposed_harmonized_title": "DOC RECORD INVESTIGAÇÕES",
                "category": "Documentário",
                "proposed_category": "Jornalismo",
                "repeat_code": "N",
                "reconciliation_key": "REC_20260731_2245",
                "programme_before_title": "DOC RECORD - REPRISA",
                "mismatch_type": "Category Mismatch",
                "is_new_programme": 1,
                "status": "Open",
                "delivery_cycle": "Initial Delivery",
                "feedback_comments": "Emissora sugeriu alteração da categoria para Jornalismo.",
                "deadline": deadline_time
            },
            {
                "channel_code": "SBT",
                "broadcast_date": today - datetime.timedelta(days=1),
                "start_time": "18:30",
                "end_time": "19:45",
                "original_title": "CIRCUS CELEBRITY SPECIAL",
                "subtitle": "Edição de Aniversário",
                "harmonized_title": "CIRCUS CELEBRITY",
                "proposed_harmonized_title": "SBT SHOW CELEBRIDADES",
                "category": "Variedades",
                "proposed_category": "Entretenimento",
                "repeat_code": "N",
                "reconciliation_key": "SBT_20260730_1830",
                "programme_before_title": "PROGRAMA DO RATINHO",
                "mismatch_type": "Title Mismatch",
                "is_new_programme": 1,
                "status": "Accepted",
                "delivery_cycle": "First Redelivery",
                "feedback_comments": "Aprovado com ressalvas no título harmonizado.",
                "deadline": deadline_time
            },
            # Divergências de Grade (Programme Differences)
            {
                "channel_code": "BAND",
                "broadcast_date": today,
                "start_time": "16:00",
                "end_time": "17:30",
                "original_title": "BRASIL URGENTE - EDICAO EXTRA",
                "subtitle": "Plantão ao Vivo",
                "harmonized_title": "BRASIL URGENTE",
                "category": "Jornalismo",
                "reconciliation_key": "BND_20260731_1600",
                "programme_before_title": "SUPER PODEROSAS",
                "mismatch_type": "Divergência de Horário / Substituição de Grade",
                "is_new_programme": 0,
                "status": "Open",
                "delivery_cycle": "Initial Delivery",
                "feedback_comments": "Programa 'Super Poderosas' foi cancelado e substituído por plantão jornalístico.",
                "deadline": deadline_time
            },
            {
                "channel_code": "RADIO_CBN",
                "broadcast_date": today,
                "start_time": "09:00",
                "end_time": "10:00",
                "original_title": "CBN MADRUGADA NOTICIAS",
                "subtitle": "",
                "harmonized_title": "CBN MANHÃ",
                "category": "Radiojornalismo",
                "reconciliation_key": "CBN_20260731_0900",
                "programme_before_title": "CBN PRIMEIRA EDICAO",
                "mismatch_type": "Title Mismatch",
                "is_new_programme": 0,
                "status": "Feedback Submitted",
                "delivery_cycle": "Initial Delivery",
                "feedback_comments": "Revisão solicitada à gerência da Rádio.",
                "deadline": deadline_time
            },
            {
                "channel_code": "GLOBO_ONLINE",
                "broadcast_date": today,
                "start_time": "20:00",
                "end_time": "21:00",
                "original_title": "TRANSMISSAO AO VIVO - PODCAST G1",
                "subtitle": "Episódio 42",
                "harmonized_title": "PODCAST G1",
                "category": "Online / Digital",
                "reconciliation_key": "G1_20260731_2000",
                "programme_before_title": "REPLAY JORNAL NACIONAL",
                "mismatch_type": "Divergência de Formato Digital",
                "is_new_programme": 0,
                "status": "Resolved",
                "delivery_cycle": "First Redelivery",
                "feedback_comments": "Ajustado e reconciliado na base central.",
                "deadline": deadline_time
            }
        ]

        for p_data in programmes_data:
            prog = Programme(**p_data)
            db.add(prog)

        # 3. Spot Differences (Reconciliação de Comerciais/Spots)
        spots_data = [
            {
                "channel_code": "TV_GLOBO",
                "broadcast_date": today,
                "delivery_cycle": "Initial Delivery",
                "spot_title": "MCDONALDS - NOVO BIG MAC CRISPY 30s",
                "advertiser": "ARCOS DOURADOS / MCDONALDS",
                "planned_time": "14:22:10",
                "monitored_time": "14:28:45",
                "discrepancy_type": "Timing Difference",
                "status": "Open",
                "comments": "Comercial veiculado no segundo break com 6m35s de atraso referente ao horário planejado."
            },
            {
                "channel_code": "RECORD_TV",
                "broadcast_date": today,
                "delivery_cycle": "Initial Delivery",
                "spot_title": "SANTANDER - CARTAO UNLIMITED 15s",
                "advertiser": "BANCO SANTANDER BRASIL",
                "planned_time": "22:50:00",
                "monitored_time": "",
                "discrepancy_type": "Missing Spot",
                "status": "Feedback Submitted",
                "comments": "Comercial não detectado no bloco planejado. Solicitação de verificação AsRun enviada."
            },
            {
                "channel_code": "SBT",
                "broadcast_date": today - datetime.timedelta(days=1),
                "delivery_cycle": "First Redelivery",
                "spot_title": "AMBEV - CERVEJA BRAHMA DUPLO MALTE 30s",
                "advertiser": "AMBEV S.A.",
                "planned_time": "",
                "monitored_time": "19:12:05",
                "discrepancy_type": "Additional Spot",
                "status": "Accepted",
                "comments": "Comercial extra veiculado sem prévio agendamento em arquivo de planejamento."
            },
            {
                "channel_code": "BAND",
                "broadcast_date": today,
                "delivery_cycle": "Initial Delivery",
                "spot_title": "COCA COLA - ZERO ACUCAR REFRESH 30s",
                "advertiser": "COCA-COLA FEMSA",
                "planned_time": "16:45:00",
                "monitored_time": "17:10:00",
                "discrepancy_type": "Break Discrepancy",
                "status": "New",
                "comments": "Break comercial remanejado devido à transmissão de plantão jornalístico ao vivo."
            }
        ]

        for s_data in spots_data:
            spot = SpotDifference(**s_data)
            db.add(spot)

        # 4. KPI Metrics
        kpi_data = [
            {"metric_name": "Novos Programas Criados (Mês)", "category": "Feedback Activity", "value": 142.0, "unit": "count", "media_type": "TV", "delivery_cycle": "Initial Delivery"},
            {"metric_name": "Divergências de Grade Abertas", "category": "Feedback Activity", "value": 28.0, "unit": "count", "media_type": "TV", "delivery_cycle": "Initial Delivery"},
            {"metric_name": "Divergências de Spots Abertas", "category": "Feedback Activity", "value": 19.0, "unit": "count", "media_type": "TV", "delivery_cycle": "Initial Delivery"},
            {"metric_name": "Conformidade de SLA (% Prazos)", "category": "Workflow", "value": 94.5, "unit": "percentage", "media_type": "TV", "delivery_cycle": "Initial Delivery"},
            {"metric_name": "Taxa de Sucesso de Arquivos AsRun", "category": "AsRun", "value": 98.2, "unit": "percentage", "media_type": "TV", "delivery_cycle": "Initial Delivery"},
            {"metric_name": "Match Rate Planejado vs Monitorado", "category": "Spot Planning", "value": 96.8, "unit": "percentage", "media_type": "TV", "delivery_cycle": "Initial Delivery"},
            {"metric_name": "Correções de Metadados por Canal", "category": "Quality", "value": 12.0, "unit": "count", "channel_code": "TV_GLOBO", "media_type": "TV"}
        ]

        for k_data in kpi_data:
            kpi = KpiMetric(**k_data)
            db.add(kpi)

        db.commit()
        print("Seed finalizado com sucesso no PostgreSQL (nielsen_db)!")
    except Exception as e:
        db.rollback()
        print(f"Erro ao popular banco de dados: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
