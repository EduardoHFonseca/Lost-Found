# Validador & Consistenciador de CNPJ — Plano do Projeto & Backlog

## Visão Geral
Sistema analítico de normalização, consistenciação e linhagem societária 360° para dados cadastrais de anunciantes, marcas e holdings corporativas.

## Arquitetura e Stack
- **Frontend & Visualização:** Streamlit (Porta 8501)
- **Backend & Core Engine:** Python 3.10, SQLAlchemy, Pandas, Regex
- **Banco de Dados:** PostgreSQL (`validador_cnpj_db`)
- **Segurança & Auditoria:** OWASP Top 10, sanitização de inputs, ausência de credenciais expostas

---

## Funcionalidades Implementadas

### 1. Módulo de Marcas & Linhagem Societária (Holding 360°)
- Resolução completa da cadeia corporativa: `Marca / Produto ➔ Anunciante Fantasia ➔ Razão Social ➔ CNPJ ➔ Grupo Econômico`.
- Cobertura dos grandes conglomerados: **Grupo CCR**, **Grupo Neoenergia**, **Grupo Votorantim** e extensibilidade para novos grupos.

### 2. Motor de Avaliação Semântica e Consistência de Marcas
- Identificação contextual da relação entre o produto/marca e o anunciante:
  - `MARCA_DIRETA` (Score 90–100%): Correspondência direta com razão social ou subsidiárias.
  - `CAMPANHA_INSTITUCIONAL` / `CAMPANHA_SOCIAL` (Score 70–90%): Linhas e campanhas operacionais legítimas.
  - `PATROCINIO_CHANCELADO` / `PATROCINIO_ESPORTIVO` (Score 45–75%): Eventos culturais e competições esportivas.
  - `BAIXA_ADERENCIA` (Score < 40%): Termos divergentes ou ruídos cadastrais.
- Coluna explicativa **Diagnóstico de Consistência** na grid e relatórios exportados.

### 3. Exibição e Relatórios com Duplo CNPJ
- Grid e exportações (CSV e Excel) contemplando explicitamente:
  - `CNPJ Grupo Econômico` (Holding controladora)
  - `CNPJ Razão Social` (Empresa / Subsidiária executora)
  - Indicador `É Matriz?` (`Verdadeiro` / `Falso`)

### 4. Gestão de Lotes e Isolamento de Testes
- Limpeza física e reset de sequências no banco de dados.
- Lote Canônico ativo com os **483 registros originais**.
- Suíte de testes automatizados (`tests/test_suite.py`) com 8 testes unitários (100% de aprovação) e cleanup isolado.

---

## Validação de Segurança
- [x] Verificação de exposição de API Keys e credenciais no código-fonte.
- [x] Inclusão de `.env` e arquivos de log no `.gitignore`.
- [x] Sanitização de campos de texto e isolamento de consultas com parâmetros tipados.

---

## Backlog / Próximos Passos
- [ ] Implementação de enriquecimento assíncrono em lote via APIs da Receita Federal / BrasilAPI.
- [ ] Exportação de relatórios em formato PDF com árvore gráfica de holdings.
- [ ] Interface de mediação manual para registros classificados como `BAIXA_ADERENCIA`.
