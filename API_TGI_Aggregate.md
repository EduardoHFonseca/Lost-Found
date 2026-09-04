# Projeto: API TGI Aggregate

## 1. Visão Geral
Módulo analítico e integrador para consumo dos serviços da **TGI Cloud Services API v3** (Kantar / IBOPE). O projeto provê conectividade, consulta automatizada ao dicionário hierárquico de variáveis e apuração em tempo real de audiências, projeções populacionais `(000)`, penetrações `(Horz % / Vert %)` e índices de afinidade `(Index)` para bases de pesquisa de mercado da América Latina.

---

## 2. Parâmetros do Ambiente & Autenticação

- **Base de Serviços:** `https://www.tgicloudservices.com/tgiapiv3`
- **Guia do Desenvolvedor:** `https://www.tgicloudservices.com/tgiapiv3/Guide/`
- **Ambiente Master (_TGI_Latina):**
  - **ACCS Client:** `_TGI_Latina`
  - **Usuários Habilitados:** `eduardo.fonseca@ibope.com`, `antonio@ibope.com`
  - **Validade:** Até o ano **2050**.
- **Ambiente de Homologação / Trial (LAT_Trial_Teste):**
  - **ACCS Client:** `LAT_Trial_Teste`
  - **Usuário Habilitado:** `trial@apikmr.com`
- **Segurança de Credenciais:** As chaves de acesso são gerenciadas via variáveis de ambiente (`.env`) e no `localStorage` do cliente/parâmetros de query, impedindo a exposição no código estático ou repositórios públicos/privados.

---

## 3. Bases de Pesquisa Homologadas

### Base 1: BASE TRIAL BRASIL
- **Título do Estudo:** BASE TRIAL BRASIL
- **Nome Técnico / ID:** `capacitabr2023r4__pw_cl`
- **Survey Family:** `bratgiptb`
- **Wave Name:** `treinamento2_p`
- **Tamanho da Amostra:** **24.576** respondentes reais
- **Unidades Amostrais (Fieldwork Units):** 5
- **Idiomas Suportados:** `ptb` (Português Brasil - default), `esp` (Espanhol), `eng` (Inglês)
- **Data da Última Publicação:** `23-07-2026`
- **Universo Populacional Projetado:** **91.616,00 mil** indivíduos
  - Homens (`MDPDSXMS`): **44.073,54 mil** (48,11%) &bull; Amostra: 11.335
  - Mulheres (`MDPDSXFM`): **47.542,46 mil** (51,89%) &bull; Amostra: 13.241

### Base 2: TG BR 2023 R3
- **Título do Estudo:** TG BR 2023 R3
- **Nome Técnico / ID:** `br2023r3_cb_pw_cl`
- **Survey Family:** `bratgiptb`
- **Wave Name:** `2023r3_p`
- **Tamanho da Amostra:** **24.576** respondentes reais
- **Unidades Amostrais (Fieldwork Units):** 207.327.920
- **Idiomas Suportados:** `ptb` (Português Brasil - default), `esp` (Espanhol), `eng` (Inglês)
- **Data da Última Publicação:** `17-06-2024`
- **Universo Populacional Projetado:** **91.616,00 mil** indivíduos
  - Homens (`MDPDSXMS`): **44.073,54 mil** (48,11%) &bull; Amostra: 11.339
  - Mulheres (`MDPDSXFM`): **47.542,46 mil** (51,89%) &bull; Amostra: 13.237

---

## 4. Endpoints Mapeados da API TGI

1. **Listagem de Pesquisas:**
   - `GET /aggregate_api/surveys?userid={user}&apikey={key}`
2. **Informações Detalhadas da Pesquisa:**
   - `GET /aggregate_api/survey/{surveyId}/wave/{waveId}/info?userid={user}&apikey={key}`
3. **Navegação do Dicionário Hierárquico:**
   - `GET /aggregate_api/survey/{surveyId}/wave/{waveId}/dictionary/{lang}/level/{levelId}?userid={user}&apikey={key}`
   - `root`: 38 grandes setores da pesquisa.
4. **Detalhe de Perguntas e Variáveis:**
   - `GET /aggregate_api/survey/{surveyId}/wave/{waveId}/dictionary/{lang}/question/{questionId}?userid={user}&apikey={key}`
5. **Cálculo de Expressões (Métricas Oficiais):**
   - `POST /aggregate_api/survey/{surveyId}/wave/{waveId}/report/expression?base64=false&userid={user}&apikey={key}`
   - *Payload:* String JSON contendo a expressão booleana (ex: `"14W157052183 AND MDPDSXMS"`).
   - *Retorno:* Cinco métricas oficiais: `(000)` Projeção Populacional, `Vert %`, `Horz %`, `Index` e `Sample`.

---

## 5. Resultados de Audiência & Gênero Apurados (Streaming)

### A. Streaming de Vídeo Pago (Últimos 30 Dias) — Keyword: `14W157052183`

- **Base 1 (BASE TRIAL BRASIL - `treinamento2_p`):**
  - **População Total:** 50.093,05 mil indivíduos (54,68% de penetração na base)
  - **Amostra:** 13.918 respondentes
  - **Distribuição de Gênero:**
    - **Homens:** **47,7%** (23.891,37 mil indivíduos | Amostra: 6.579)
    - **Mulheres:** **52,3%** (26.201,68 mil indivíduos | Amostra: 7.339)
  - **Netflix (U30d - `14W155621113`):** Total 41.298,81 mil (Amostra 11.337) &bull; Homens: 46,6% vs Mulheres: 53,4%

- **Base 2 (TG BR 2023 R3 - `2023r3_p`):**
  - **População Total:** 49.574,03 mil indivíduos (54,11% de penetração na base)
  - **Amostra:** 13.786 respondentes
  - **Distribuição de Gênero:**
    - **Homens:** **47,4%** (23.498,39 mil indivíduos | Amostra: 6.473)
    - **Mulheres:** **52,6%** (26.075,64 mil indivíduos | Amostra: 7.313)

### B. Streaming de Música (Costuma Ouvir) — Keyword: `B221542445`

- **Base 1 (BASE TRIAL BRASIL - `treinamento2_p`):**
  - **População Total:** 47.030,41 mil indivíduos (51,33% de penetração na base)
  - **Amostra:** 12.873 respondentes
  - **Distribuição de Gênero:**
    - **Homens:** **49,2%** (23.143,47 mil indivíduos | Amostra: 6.281)
    - **Mulheres:** **50,8%** (23.886,94 mil indivíduos | Amostra: 6.592)
  - **Spotify (U30d - `B221538003`):** Total 28.209,49 mil (Amostra 7.759) &bull; Homens: 48,9% vs Mulheres: 51,1%

- **Base 2 (TG BR 2023 R3 - `2023r3_p`):**
  - **População Total:** 44.278,31 mil indivíduos (48,33% de penetração na base)
  - **Amostra:** 12.296 respondentes
  - **Distribuição de Gênero:**
    - **Homens:** **49,5%** (21.909,94 mil indivíduos | Amostra: 6.003)
    - **Mulheres:** **50,5%** (22.368,37 mil indivíduos | Amostra: 6.293)

---

## 6. Dashboard de Visualização

- **Hospedagem Estática:** Publicado no **here.now**.
- **URLs Ativas:**
  - Versão Atual (Multi-Base + Tratamento de Erro 401): [https://spruce-riddle-dwmd.here.now/](https://spruce-riddle-dwmd.here.now/)
  - Versões Anteriores: [https://supple-tassel-q97y.here.now/](https://supple-tassel-q97y.here.now/) | [https://plush-bloom-5dp2.here.now/](https://plush-bloom-5dp2.here.now/) | [https://ancient-lagoon-j6mn.here.now/](https://ancient-lagoon-j6mn.here.now/)
- **Código Fonte do Dashboard:** Localizado em `api-tgi-aggregate/index.html`.
- **Recursos do Dashboard:**
  - Seletor rápido de base ativa no topo (`BASE TRIAL BRASIL` vs `TG BR 2023 R3`).
  - Atualização instantânea de metadados, Universo Populacional, amostras e unidades amostrais.
  - Card dedicado de Streaming com abertura automática de dados de gênero (% Homens / % Mulheres), distribuição e benchmarks (Netflix e Spotify) ajustados para a base selecionada.
  - Painel de consulta dinâmica de expressões com feedback em tempo real, skeleton loader, alertas preventivos e operadores booleanos (`AND`, `OR`, `NOT`).
  - **Dicionário Interativo de Variáveis & Expressões:**
    - Catálogo curado com mais de 30 variáveis essenciais (Demografia: `MDPDSXMS`, `MDPDSXFM`; Faixas Etárias: `MDPDRE12` a `MDPDRE65`; Classes Sociais Critério Brasil: `NSEBRA01`, `O31982684`, `O31982685`, `NSEBRA02`, `NSEBRA03`; Regiões: `SAOPAULO`, `RIODEJAN`, etc.; Streaming por Plataforma: Netflix `14W155621113`, Prime Video `18W1767682`, Disney+ `22W1536487`, Globoplay `17W1536438`, HBO Max `17W1768326`, Spotify `B221538003`).
    - Navegador em Árvore Oficial via API TGI (`/dictionary/{lang}/level/{levelId}` e `/question/{questionId}`) com drilldown em tempo real e extração de keywords com 1 clique (`Usar` ou `+ AND`).
  - Dicionário setorial dinâmico (38 categorias para Base 1 e 40 categorias para Base 2, incluindo o setor dedicado `STREMUSIC`).
  - Modal seguro para inserção e alternância de credenciais por base sem persistência no código fonte.

---

## 7. Diretrizes de Segurança (OWASP Top 10)

- [x] Nenhuma chave de API exposta estaticamente no código-fonte ou no repositório.
- [x] Requisições parametrizadas e sanitizadas para evitar injeções.
- [x] Gestão de credenciais via `localStorage` e `.env`.
- [x] **Item Obrigatório de Backlog:** A validação de segurança referente à exposição de API Keys e credenciais deve permanecer no backlog até nova auditoria formal de release.

---

## 8. Backlog do Projeto (Próximas Fases)

- [ ] **Validação de Segurança:** Executar varredura automatizada contra vazamento de credenciais antes de qualquer publicação em ambiente produtivo.
- [ ] **Módulo Backend em Python:** Criar cliente wrapper (`services/tgi_client.py`) para chamadas server-side com cálculo de hash SHA-1 (`sha1(ts + privatekey + publickey)`).
- [ ] **Motor de Tabulação Cruzada (Crosstab):** Integrar chamadas avançadas para matrizes de linhas e colunas (crosstabs de até 800x800).
- [ ] **Exportador de Audiências:** Permitir download de relatórios em formato CSV e Excel formatados com as 5 métricas padrão.
- [ ] **Mapeamento de Demais Bases LatAm:** Expandir a seleção para outras pesquisas cobertas pelo contrato master `_TGI_Latina`.
