# Projeto: API TGI Aggregate

## 1. Visão Geral
Módulo analítico e integrador para consumo dos serviços da **TGI Cloud Services API v3** (Kantar / IBOPE). O projeto provê conectividade, consulta automatizada ao dicionário hierárquico de variáveis e apuração em tempo real de audiências, projeções populacionais `(000)`, penetrações `(Horz % / Vert %)` e índices de afinidade `(Index)` para bases de pesquisa de mercado da América Latina.

---

## 2. Parâmetros do Ambiente & Autenticação

- **Base de Serviços:** `https://www.tgicloudservices.com/tgiapiv3`
- **Guia do Desenvolvedor:** `https://www.tgicloudservices.com/tgiapiv3/Guide/`
- **ACCS Client / Company Master:** `_TGI_Latina`
  - *Nota:* Ambiente master configurado para conceder acesso centralizado e facilitar expansões futuras para quaisquer bases ou países da América Latina.
- **Usuários Habilitados:**
  - `eduardo.fonseca@ibope.com`
  - `antonio@ibope.com`
- **Validade do Acesso:** Configurada até o ano **2050**.
- **Segurança de Credenciais:** As chaves de acesso são gerenciadas via variáveis de ambiente (`.env`) e no `localStorage` do cliente, impedindo a exposição no código estático ou repositórios públicos/privados.

---

## 3. Base Ativa: BASE TRIAL BRASIL

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
- **População Total:** 50.093,05 mil indivíduos (54,68% de penetração na base)
- **Amostra:** 13.918 respondentes
- **Distribuição de Gênero:**
  - **Homens:** **47,7%** (23.891,37 mil indivíduos | Amostra: 6.579)
  - **Mulheres:** **52,3%** (26.201,68 mil indivíduos | Amostra: 7.339)
- **Plataforma em Destaque — Netflix (U30d - `14W155621113`):**
  - Total: 41.298,81 mil indivíduos (Amostra: 11.337)
  - Homens: **46,6%** (19.229,54 mil) vs Mulheres: **53,4%** (22.069,27 mil)

### B. Streaming de Música (Costuma Ouvir) — Keyword: `B221542445`
- **População Total:** 47.030,41 mil indivíduos (51,33% de penetração na base)
- **Amostra:** 12.873 respondentes
- **Distribuição de Gênero:**
  - **Homens:** **49,2%** (23.143,47 mil indivíduos | Amostra: 6.281)
  - **Mulheres:** **50,8%** (23.886,94 mil indivíduos | Amostra: 6.592)
- **Plataforma em Destaque — Spotify (U30d - `B221538003`):**
  - Total: 28.209,49 mil indivíduos (Amostra: 7.759)
  - Homens: **48,9%** (13.787,12 mil) vs Mulheres: **51,1%** (14.422,37 mil)

---

## 6. Dashboard de Visualização

- **Hospedagem Estática:** Publicado no **here.now**.
- **URL Ativa:** [https://ancient-lagoon-j6mn.here.now/](https://ancient-lagoon-j6mn.here.now/)
- **Código Fonte do Dashboard:** Localizado em `api-tgi-aggregate/index.html`.
- **Recursos do Dashboard:**
  - Exibição executiva dos metadados e parâmetros da pesquisa.
  - Card dedicado de Streaming com abertura detalhada de dados de gênero (% Homens / % Mulheres) e barras comparativas.
  - Painel de consulta dinâmica de expressões com benchmarks de estado civil e operadores lógicos (`AND`, `OR`, `NOT`).
  - Matriz das 38 categorias temáticas com identificadores e keywords.
  - Modal seguro para inserção e alternância de credenciais sem persistência no código fonte.

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
