import os
import io
import pandas as pd
import streamlit as st
from datetime import datetime
from sqlalchemy.orm import Session

# Importações internas do projeto
from database.database import SessionLocal, init_db
from database.models import LoteIngestao, Anunciante, MediacaoOperador, ConsultaCNPJCache
from core.cnpj_engine import validate_cnpj, format_cnpj, clean_cnpj, generate_cnpj, is_matriz, extract_cnpj_root
from processors.batch_processor import process_batch_file
from services.enrichment import enrich_cnpj_info


# Configuração inicial da página Streamlit
st.set_page_config(
    page_title="Validador & Consistenciador de CNPJ",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa as tabelas do PostgreSQL no arranque
init_db()


def get_db_session():
    return SessionLocal()


# --- CSS Customizado para Estilização Profissional ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .badge-ok {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-warn {
        background-color: #fef9c3;
        color: #854d0e;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-error {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .card-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar - Informações e Configuração de Lote
st.sidebar.image("https://img.icons8.com/color/96/verified-badge.png", width=64)
st.sidebar.title("Validador CNPJ")
st.sidebar.caption("Consistenciador de Anunciantes & TV")

db = get_db_session()

# Obter Lotes
lotes = db.query(LoteIngestao).order_by(LoteIngestao.id.desc()).all()
lote_selecionado_id = None

if lotes:
    lote_options = {f"Lote #{l.id} - {l.nome_arquivo} ({l.data_importacao.strftime('%d/%m/%Y %H:%M')})": l.id for l in lotes}
    sel_label = st.sidebar.selectbox("Selecione o Lote de Trabalho:", list(lote_options.keys()))
    lote_selecionado_id = lote_options[sel_label]
else:
    st.sidebar.info("Nenhum lote importado ainda. Faça o upload na Aba 1.")

st.sidebar.markdown("---")
st.sidebar.markdown("**Serviços de Dados:**")
st.sidebar.markdown("✅ PostgreSQL Local (`validador_cnpj_db`)\n✅ Cache D+0\n✅ BrasilAPI / ReceitaWS")


# --- TÍTULO PRINCIPAL ---
st.markdown("<div class='main-header'>🔍 Validador e Consistenciador de CNPJ</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Normalização, detecção de divergências de Matriz/Filial, enriquecimento de dados e mediação de marcas (Problem Statement)</div>", unsafe_allow_html=True)


# ABAS NAVEGÁVEIS
tab1, tab2, tab3, tab4 = st.tabs([
    "📁 1. Carga & Ingestão",
    "📊 2. Painel Geral (KPIs)",
    "⚖️ 3. Caixa de Entrada & Mediação",
    "📥 4. Exportação & Ferramentas"
])


# ==============================================================================
# ABA 1: CARGA E INGESTÃO DE LOTES
# ==============================================================================
with tab1:
    st.subheader("Carga de Arquivos em Massa (CSV ou XLSX)")
    st.markdown("Faça o upload do arquivo contendo os anunciantes (ex: `Lista Entrega CNPJ´s.csv`). O sistema irá carregar, sanitizar os CNPJs e identificar inconsistências para mediação.")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader("Selecione o arquivo de anunciantes:", type=["csv", "xlsx", "xls"])
        use_net = st.checkbox("Consultar APIs externas para CNPJs não armazenados em cache (BrasilAPI / ReceitaWS)", value=False, help="Marque para buscar dados da Receita em tempo real para novos CNPJs. Se desmarcado, utiliza cache do PostgreSQL e validação matemática de alta velocidade.")

        if uploaded_file is not None:
            if st.button("🚀 Processar e Carregar no PostgreSQL", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_prog(p):
                    progress_bar.progress(p)
                    status_text.text(f"Processando lote... {p}% concluído")

                lote, objs = process_batch_file(
                    uploaded_file,
                    uploaded_file.name,
                    db,
                    use_network=use_net,
                    progress_callback=update_prog
                )
                
                st.success(f"Lote #{lote.id} ('{lote.nome_arquivo}') processado e gravado com sucesso no PostgreSQL!")
                st.balloons()
                st.rerun()

    with col2:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.markdown("#### 📋 Formato de Entrada Esperado")
        st.markdown("""
        O arquivo pode conter as seguintes colunas padrão:
        - `Cod Anunciante Razão`
        - `Anunciante Rz Social`
        - `CNPJ`
        - `Cod Anunc Fantasia`
        - `Anunciante Fantasia`
        
        *Obs: CNPJs sem zeros à esquerda ou não formatados serão normalizados automaticamente.*
        """)
        st.markdown("</div>", unsafe_allow_html=True)

    if lotes:
        st.markdown("---")
        st.subheader("📦 Historico de Lotes Processados no Banco de Dados")
        
        lotes_df = pd.DataFrame([{
            "ID Lote": l.id,
            "Nome do Arquivo": l.nome_arquivo,
            "Data da Carga": l.data_importacao.strftime("%d/%m/%Y %H:%M:%S"),
            "Total de Registros": l.total_linhas,
            "Válidos OK": l.total_validos,
            "Inconsistentes / Mediação": l.total_inconsistentes,
            "Isentos / Pessoa Física": l.total_isentos_pf,
            "Status": l.status_lote
        } for l in lotes])

        st.dataframe(lotes_df, use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 2: PAINEL GERAL & KPIS
# ==============================================================================
with tab2:
    if not lote_selecionado_id:
        st.warning("Selecione ou carregue um Lote na Aba 1 para visualizar os dados.")
    else:
        lote_atual = db.query(LoteIngestao).filter(LoteIngestao.id == lote_selecionado_id).first()
        
        # Métricas no Topo
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Anunciantes", f"{lote_atual.total_linhas:,}")
        m2.metric("🟢 Válidos & Matriz OK", f"{lote_atual.total_validos:,}", f"{((lote_atual.total_validos/lote_atual.total_linhas)*100):.1f}%")
        m3.metric("🟡 Requer Mediação", f"{lote_atual.total_inconsistentes:,}", delta_color="inverse")
        m4.metric("⚪ Isentos / Pessoa Física", f"{lote_atual.total_isentos_pf:,}")

        st.markdown("---")

        # Filtros de Tabela
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1:
            status_filter = st.selectbox("Filtrar por Status de Validação:", [
                "TODOS", "REQUER_MEDIACAO", "VALIDO_OK", "RESOLVIDO_MANUAL", "ISENTO_PF"
            ])
        with col_f2:
            div_filter = st.selectbox("Filtrar por Tipo de Divergência:", [
                "TODOS", "CNPJ_DUPLICADO_OUTRA_RAZAO", "FILIAL_EM_RAIZ", "CNPJ_INATIVO", "CNPJ_INVALIDO_DV", "SEM_CNPJ"
            ])
        with col_f3:
            search_text = st.text_input("🔍 Buscar por Razão Social, Fantasia ou CNPJ:")

        # Query no PostgreSQL
        query = db.query(Anunciante).filter(Anunciante.lote_id == lote_selecionado_id)
        
        if status_filter != "TODOS":
            query = query.filter(Anunciante.status_validacao == status_filter)
        if div_filter != "TODOS":
            query = query.filter(Anunciante.tipo_divergencia == div_filter)
        
        results = query.all()

        # Filtro em memória por texto de busca
        if search_text:
            stext = search_text.lower().strip()
            results = [
                r for r in results
                if stext in (r.anunciante_rz_social or "").lower()
                or stext in (r.anunciante_fantasia or "").lower()
                or stext in (r.cnpj_formatado or "").lower()
                or stext in (r.cnpj_original or "").lower()
                or stext in (r.cod_anunciante_razao or "").lower()
            ]

        st.caption(f"Exibindo {len(results)} registros encontrados.")

        if results:
            data_list = []
            for r in results:
                data_list.append({
                    "ID": r.id,
                    "Cód. Rz": r.cod_anunciante_razao,
                    "Razão Social (Base)": r.anunciante_rz_social,
                    "CNPJ Formatado": r.cnpj_formatado or "---",
                    "Status Receita": r.situacao_cadastral or "---",
                    "Cód. Fantasia": r.cod_anunc_fantasia,
                    "Nome Fantasia": r.anunciante_fantasia,
                    "É Matriz?": "Sim (/0001)" if r.eh_matriz is True else ("Não (Filial)" if r.eh_matriz is False else "---"),
                    "Status Validação": r.status_validacao,
                    "Divergência / Alerta": r.tipo_divergencia or "Nenhuma",
                    "Última Atualização": r.data_ultima_atualizacao.strftime("%d/%m/%Y %H:%M") if r.data_ultima_atualizacao else "---"
                })

            grid_df = pd.DataFrame(data_list)
            st.dataframe(grid_df, use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 3: CAIXA DE ENTRADA & MEDIAÇÃO (HUMAN-IN-THE-LOOP)
# ==============================================================================
with tab3:
    st.subheader("⚖️ Central de Decisão e Mediação do Operador")
    st.markdown("Atenda aos casos de ambiguidades, compartilhamento de CNPJ entre anunciantes diferentes (ex: *McDonald's x Arcos Dourados*), filiais e empresas inativas.")

    if not lote_selecionado_id:
        st.warning("Selecione um Lote na barra lateral.")
    else:
        # Busca apenas casos que exigem mediação
        pendentes = db.query(Anunciante).filter(
            Anunciante.lote_id == lote_selecionado_id,
            Anunciante.status_validacao == "REQUER_MEDIACAO"
        ).all()

        if not pendentes:
            st.success("🎉 Parabéns! Não há casos pendentes de mediação para este lote. Todos os CNPJs foram consistenciados ou resolvidos!")
        else:
            st.info(f"Há **{len(pendentes)}** anunciantes com inconsistências pendentes de análise humana neste lote.")

            # Agrupa os pendentes por tipo de divergência
            tipos_div = sorted(list(set(p.tipo_divergencia for p in pendentes if p.tipo_divergencia)))
            sel_div_type = st.selectbox("Filtrar Fila por Categoria de Problema:", tipos_div)

            itens_categoria = [p for p in pendentes if p.tipo_divergencia == sel_div_type]

            # Seleção do item a analisar
            item_labels = {f"#{p.id} | Cod: {p.cod_anunciante_razao} | {p.anunciante_fantasia or p.anunciante_rz_social} | CNPJ: {p.cnpj_formatado or p.cnpj_original}": p.id for p in itens_categoria}
            
            sel_item_label = st.selectbox("Selecione o Anunciante para Analisar e Decidir:", list(item_labels.keys()))
            anunciante_id_sel = item_labels[sel_item_label]

            item_atual = db.query(Anunciante).filter(Anunciante.id == anunciante_id_sel).first()

            st.markdown("---")

            # EXIBIÇÃO DE CASO ESPECIAL: CNPJ DUPLICADO EM OUTRAS RAZÕES (Ex: McDonald's x Arcos Dourados)
            if item_atual.tipo_divergencia == "CNPJ_DUPLICADO_OUTRA_RAZAO":
                st.warning("⚠️ **CONFLITO DE CNPJ COMPARTILHADO DETECTADO**: O mesmo número de CNPJ está associado a múltiplos códigos ou marcas distintas de anunciante na base!")

                # Busca todos os anunciantes que possuem o mesmo CNPJ limpo
                concorrentes = db.query(Anunciante).filter(
                    Anunciante.lote_id == lote_selecionado_id,
                    Anunciante.cnpj_limpo == item_atual.cnpj_limpo
                ).all()

                st.markdown("#### 🔀 Anunciantes em Conflito Compartilhando o mesmo CNPJ:")
                
                cols = st.columns(len(concorrentes) if len(concorrentes) <= 3 else 3)
                for idx, c in enumerate(concorrentes):
                    with cols[idx % 3]:
                        st.markdown(f"""
                        <div class='card-box'>
                            <h4>Anunciante Cód. {c.cod_anunciante_razao}</h4>
                            <b>Razão Social:</b> {c.anunciante_rz_social}<br/>
                            <b>Nome Fantasia:</b> {c.anunciante_fantasia} (Cód: {c.cod_anunc_fantasia})<br/>
                            <b>CNPJ Cadastrado:</b> {c.cnpj_formatado}<br/>
                            <b>Status Atual:</b> {c.status_validacao}
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                st.markdown("### 🛠️ Decisão do Operador (Resolução de Conflito Commercial)")

                with st.form(key=f"form_mediacao_{item_atual.id}"):
                    opcao = st.radio(
                        "Qual ação deseja aplicar para resolver este conflito de cadastro?",
                        [
                            "1. UNIFICAR_ANUNCIANTES (Junta as duas marcas sob o mesmo cadastro e CNPJ)",
                            "2. ALTERAR_CODIGO (Corrige o código do anunciante secundário preservando o CNPJ)",
                            "3. MANTER_AMBOS (Aprova exceção comercial para manter ambos com o mesmo CNPJ)",
                            "4. TROCAR_PARA_FILIAL (Atribui um CNPJ de Filial / Secundário para um dos anunciantes)",
                            "5. MARCAR_ISENTO (Marca um deles como Isento/Pessoa Física sem exigência de CNPJ)"
                        ]
                    )

                    novo_cnpj_input = st.text_input("Novo CNPJ para este anunciante (necessário se escolher 'TROCAR_PARA_FILIAL'):", value=item_atual.cnpj_formatado or "")
                    operador_nome = st.text_input("Seu Identificador / E-mail de Operador:", value="operador.globo@kantar.com")
                    justificativa_text = st.text_area("Justificativa da Decisão de Mediação:", value="Aprovado ajuste após análise da regra comercial e verificação na Receita.")

                    btn_submit = st.form_submit_button("💾 Salvar Decisão de Mediação e Atualizar Registros", type="primary")

                    if btn_submit:
                        cod_opcao = opcao.split(".")[1].split("(")[0].strip()
                        
                        # Executa a ação escolhida
                        if cod_opcao == "MARCAR_ISENTO":
                            item_atual.status_validacao = "ISENTO_PF"
                            item_atual.tipo_divergencia = "SEM_CNPJ"
                            item_atual.cnpj_limpo = ""
                            item_atual.cnpj_formatado = "ISENTO"
                        else:
                            item_atual.status_validacao = "RESOLVIDO_MANUAL"
                            if cod_opcao == "TROCAR_PARA_FILIAL" and novo_cnpj_input:
                                is_v, c_clean, _ = validate_cnpj(novo_cnpj_input)
                                if is_v:
                                    item_atual.cnpj_limpo = c_clean
                                    item_atual.cnpj_formatado = format_cnpj(c_clean)
                                    item_atual.eh_matriz = is_matriz(c_clean)
                        
                        item_atual.data_ultima_atualizacao = datetime.utcnow()

                        # Registra na tabela de auditoria
                        med = MediacaoOperador(
                            anunciante_id=item_atual.id,
                            opcao_escolhida=cod_opcao,
                            cnpj_anterior=item_atual.cnpj_formatado,
                            cnpj_novo=novo_cnpj_input if cod_opcao == "TROCAR_PARA_FILIAL" else item_atual.cnpj_formatado,
                            operador_id=operador_nome,
                            justificativa=justificativa_text
                        )
                        db.add(med)
                        db.commit()

                        st.success(f"Decisão '{cod_opcao}' salva com sucesso para o Anunciante #{item_atual.id}!")
                        st.rerun()

            else:
                # DEMAIS CASOS (FILIAL_EM_RAIZ, CNPJ_INATIVO, CNPJ_INVALIDO_DV, SEM_CNPJ)
                col_d1, col_d2 = st.columns(2)

                with col_d1:
                    st.markdown("#### 📌 Registro na Base do Cliente")
                    st.write(f"**ID:** #{item_atual.id}")
                    st.write(f"**Cód. Anunciante Razão:** {item_atual.cod_anunciante_razao}")
                    st.write(f"**Razão Social:** {item_atual.anunciante_rz_social}")
                    st.write(f"**Nome Fantasia:** {item_atual.anunciante_fantasia} (Cód: {item_atual.cod_anunc_fantasia})")
                    st.write(f"**CNPJ Atual:** {item_atual.cnpj_formatado or item_atual.cnpj_original}")
                    st.write(f"**É Matriz?:** {item_atual.eh_matriz}")

                with col_d2:
                    st.markdown("#### 🏢 Diagnóstico da Receita & Recomendação")
                    st.write(f"**Problema Identificado:** `{item_atual.tipo_divergencia}`")
                    st.write(f"**Situação na Receita:** {item_atual.situacao_cadastral or 'Não consultado'}")
                    st.write(f"**Razão Social Oficial:** {item_atual.razao_social_receita or 'N/A'}")
                    st.write(f"**CNPJ Matriz Sugerido:** {item_atual.cnpj_matriz_sugerido or 'N/A'}")

                st.markdown("---")
                
                with st.form(key=f"form_mediacao_gen_{item_atual.id}"):
                    opcao = st.radio(
                        "Selecione a ação corretiva para este registro:",
                        [
                            "1. ACEITAR_MATRIZ_SUGERIDA (Atualiza o CNPJ para a Matriz Raiz /0001)",
                            "2. MANTER_FILIAL (Mantém o CNPJ de Filial como exceção de Franquia)",
                            "3. MARCAR_ISENTO (Marca como Pessoa Física / Anunciante Padrão Isento)",
                            "4. ATUALIZAR_CNPJ_MANUAL (Informa um novo CNPJ manualmente)"
                        ]
                    )

                    manual_cnpj = st.text_input("Novo CNPJ (Preencher apenas se escolher 'ATUALIZAR_CNPJ_MANUAL'):", value="")
                    operador_nome = st.text_input("Identificador do Operador:", value="operador.globo@kantar.com")
                    justificativa_text = st.text_area("Justificativa:", value="Análise efetuada e confirmada na base comercial.")

                    btn_sub_gen = st.form_submit_button("💾 Confirmar e Resolver Inconsistência", type="primary")

                    if btn_sub_gen:
                        cod_opcao = opcao.split(".")[1].split("(")[0].strip()

                        if cod_opcao == "ACEITAR_MATRIZ_SUGERIDA" and item_atual.cnpj_matriz_sugerido:
                            item_atual.cnpj_formatado = item_atual.cnpj_matriz_sugerido
                            item_atual.cnpj_limpo = clean_cnpj(item_atual.cnpj_matriz_sugerido)
                            item_atual.eh_matriz = True
                            item_atual.status_validacao = "RESOLVIDO_MANUAL"
                        elif cod_opcao == "MARCAR_ISENTO":
                            item_atual.status_validacao = "ISENTO_PF"
                            item_atual.tipo_divergencia = "SEM_CNPJ"
                            item_atual.cnpj_limpo = ""
                            item_atual.cnpj_formatado = "ISENTO"
                        elif cod_opcao == "ATUALIZAR_CNPJ_MANUAL" and manual_cnpj:
                            is_v, c_clean, _ = validate_cnpj(manual_cnpj)
                            if is_v:
                                item_atual.cnpj_limpo = c_clean
                                item_atual.cnpj_formatado = format_cnpj(c_clean)
                                item_atual.eh_matriz = is_matriz(c_clean)
                                item_atual.status_validacao = "RESOLVIDO_MANUAL"
                            else:
                                st.error("O CNPJ digitado é matematicamente inválido.")
                                st.stop()
                        else:
                            item_atual.status_validacao = "RESOLVIDO_MANUAL"

                        item_atual.data_ultima_atualizacao = datetime.utcnow()

                        med = MediacaoOperador(
                            anunciante_id=item_atual.id,
                            opcao_escolhida=cod_opcao,
                            cnpj_anterior=item_atual.cnpj_original,
                            cnpj_novo=item_atual.cnpj_formatado,
                            operador_id=operador_nome,
                            justificativa=justificativa_text
                        )
                        db.add(med)
                        db.commit()

                        st.success(f"Registro #{item_atual.id} resolvido com sucesso!")
                        st.rerun()


# ==============================================================================
# ABA 4: EXPORTAÇÃO & FERRAMENTAS
# ==============================================================================
with tab4:
    st.subheader("📥 Exportação de Relatórios & Ferramentas Auxiliares")

    if not lote_selecionado_id:
        st.warning("Selecione um Lote para exportar dados.")
    else:
        st.markdown("### 1. Exportar Base Higienizada de Anunciantes (Padrão Globo / Mercado)")
        st.markdown("Baixe o relatório com todos os CNPJs devidamente formatados (`NN.NNN.NNN/NNNN-NN`), normalizados e com status de validação.")

        all_records = db.query(Anunciante).filter(Anunciante.lote_id == lote_selecionado_id).all()

        if all_records:
            export_data = []
            for a in all_records:
                export_data.append({
                    "Cod Anunciante Razão": a.cod_anunciante_razao,
                    "Anunciante Rz Social": a.anunciante_rz_social,
                    "CNPJ Formatado": a.cnpj_formatado or "ISENTO",
                    "Cod Anunc Fantasia": a.cod_anunc_fantasia,
                    "Anunciante Fantasia": a.anunciante_fantasia,
                    "Status Validação": a.status_validacao,
                    "Situação Receita": a.situacao_cadastral,
                    "Matriz?": "SIM" if a.eh_matriz else ("NÃO" if a.eh_matriz is False else "ISENTO"),
                    "Razão Social Receita": a.razao_social_receita or "",
                    "Data Última Atualização": a.data_ultima_atualizacao.strftime("%Y-%m-%d %H:%M:%S") if a.data_ultima_atualizacao else ""
                })

            export_df = pd.DataFrame(export_data)

            col_ex1, col_ex2 = st.columns(2)

            with col_ex1:
                csv_buffer = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    label="📄 Baixar Base Higienizada em CSV",
                    data=csv_buffer,
                    file_name=f"base_anunciantes_higienizada_lote_{lote_selecionado_id}.csv",
                    mime="text/csv",
                    type="primary"
                )

            with col_ex2:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Anunciantes_Higienizados")
                
                st.download_button(
                    label="📊 Baixar Base Higienizada em Excel (.xlsx)",
                    data=excel_buffer.getvalue(),
                    file_name=f"base_anunciantes_higienizada_lote_{lote_selecionado_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        st.markdown("---")
        st.markdown("### 2. Trilha de Auditoria das Mediações (Operadores)")

        mediacoes = db.query(MediacaoOperador).all()
        if mediacoes:
            med_list = []
            for m in mediacoes:
                med_list.append({
                    "ID Mediação": m.id,
                    "ID Anunciante": m.anunciante_id,
                    "Decisão Escolhida": m.opcao_escolhida,
                    "CNPJ Anterior": m.cnpj_anterior,
                    "CNPJ Novo": m.cnpj_novo,
                    "Operador": m.operador_id,
                    "Justificativa": m.justificativa,
                    "Data/Hora": m.data_decisao.strftime("%d/%m/%Y %H:%M:%S")
                })
            med_df = pd.DataFrame(med_list)
            st.dataframe(med_df, use_container_width=True, hide_index=True)

            csv_med = med_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📑 Baixar Relatório de Auditoria das Mediações (CSV)",
                data=csv_med,
                file_name="trilha_auditoria_mediacoes.csv",
                mime="text/csv"
            )

    st.markdown("---")
    st.markdown("### 3. Ferramenta Auxiliar: Validador & Gerador Individual de CNPJ")

    col_val1, col_val2 = st.columns(2)

    with col_val1:
        st.markdown("#### Testar Validação Individual")
        test_cnpj_input = st.text_input("Digite um CNPJ para validar:", value="61.079.117/0001-05")
        if test_cnpj_input:
            is_v, c_clean, reason = validate_cnpj(test_cnpj_input)
            if is_v:
                st.success(f"✅ **VÁLIDO!** CNPJ Formatado: `{format_cnpj(c_clean)}` | É Matriz?: `{is_matriz(c_clean)}`")
            else:
                st.error(f"❌ **INVÁLIDO!** Motivo: {reason}")

    with col_val2:
        st.markdown("#### Gerador Sintético de CNPJ (Mocks de Testes)")
        tipo_gen = st.radio("Tipo de CNPJ para gerar:", ["Matriz (/0001)", "Filial (/0002+)"])
        if st.button("🎲 Gerar CNPJ Válido"):
            gen_val = generate_cnpj(matriz=(tipo_gen == "Matriz (/0001)"))
            st.info(f"CNPJ Gerado: `{gen_val}`")

db.close()
