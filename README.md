# RPA Portal da Transparência — API

Solução de automação desenvolvida em Python para consultar dados públicos de pessoas físicas no [Portal da Transparência do Governo Federal](https://portaldatransparencia.gov.br/). A API realiza scraping headless com Playwright, extrai dados de vínculos com programas sociais e notifica um webhook no n8n ao final de cada consulta — permitindo integração direta com fluxos de automação e planilhas.

## Tecnologias

- **Python 3.13**
- **FastAPI** — framework web e documentação automática (Swagger/OpenAPI)
- **Playwright** — automação headless do navegador
- **Poetry** — gerenciamento de dependências
- **Docker** — containerização da aplicação
- **slowapi** — rate limiting por IP
- **httpx** — cliente HTTP assíncrono para notificação ao n8n

## Estrutura do Projeto

```
rpa_api/
├── rpa_api/
│   ├── app.py        # Aplicação FastAPI e endpoints
│   ├── schemas.py    # Schemas Pydantic (request/response)
│   └── scraper.py    # Robô Playwright (coleta de dados)
├── tests/
├── README.md
└── pyproject.toml
```

## Variáveis de Ambiente

| Variável | Descrição | Obrigatória |
|---|---|---|
| `N8N_WEBHOOK_URL` | URL do webhook n8n para receber o resultado de cada consulta | Não |
| `PLAYWRIGHT_TIMEOUT` | Timeout das operações do Playwright em ms | Não |

Crie um arquivo `.env` na raiz do projeto para desenvolvimento local:

```env
N8N_WEBHOOK_URL=https://seu-dominio.app.n8n.cloud/webhook/consulta-transparencia
```

## Instalação e execução

### Com Docker (recomendado)

**Pré-requisito:** Docker instalado.

```bash
# Build da imagem
docker build -t rpa-transparencia .

# Rodar o container
docker run -p 8000:8000 rpa-transparencia
```

### Sem Docker

**Pré-requisitos:** Python 3.13+ e Poetry instalados.

```bash
# Instalar dependências
poetry install

# Instalar o navegador do Playwright
poetry run playwright install chromium

# Rodar em modo desenvolvimento
poetry run fastapi dev rpa_api/app.py
```

Acesse:
- API: `http://127.0.0.1:8000`
- Documentação Swagger: `http://127.0.0.1:8000/docs`
- Documentação ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### `POST /api/v1/consulta`

Inicia a automação e retorna os dados coletados do Portal da Transparência. Ao finalizar, notifica o webhook configurado em `N8N_WEBHOOK_URL` com o mesmo payload da resposta.

**Body (JSON):**

```json
{
  "nome": "João da Silva",
  "cpf": "000.000.000-00",
  "nis": "00000000000",
  "filtro_beneficiario": false
}
```

> Pelo menos um dos campos `nome`, `cpf` ou `nis` é obrigatório. `filtro_beneficiario: true` restringe a busca a beneficiários de programas sociais.

**Resposta (sucesso):**

```json
{
  "status": "sucesso",
  "nome": "NOME DA PESSOA",
  "cpf": "***.659.347-**",
  "beneficios": [
    {
      "tipo": "Nome do Programa",
      "dados": [
        { "NIS": "00000000000", "Nome": "...", "Valor Recebido": "R$ 0,00" }
      ]
    }
  ],
  "screenshot_base64": "<base64>",
  "mensagem": null
}
```

> O campo `cpf` retorna o valor mascarado exatamente como exibido pelo portal (`***.659.347-**`).

**Resposta (erro):**

```json
{
  "status": "erro",
  "beneficios": [],
  "mensagem": "Foram encontrados 0 resultados para o termo ..."
}
```

## Cenários de Teste

| Cenário | Entrada | Saída Esperada |
|---|---|---|
| Sucesso por CPF/NIS | CPF ou NIS válido | JSON com dados e screenshot |
| Erro por CPF/NIS | CPF ou NIS inexistente | JSON com mensagem de erro |
| Sucesso por Nome | Nome completo | JSON com dados do primeiro resultado |
| Erro por Nome | Nome inexistente | JSON com mensagem de erro |
| Filtrado | Sobrenome + filtro social | JSON com dados do primeiro resultado filtrado |

## Segurança e Limites

- **Rate limiting:** máximo de 5 requisições por minuto por IP. Excedido, retorna HTTP `429`.
- **Semáforo de concorrência:** máximo de 2 browsers Playwright simultâneos. Requisições excedentes aguardam na fila.
- **CORS:** habilitado para todas as origens, permitindo consumo por ferramentas externas como n8n.

## Decisões Técnicas

- **Playwright** foi escolhido por oferecer suporte nativo a execuções assíncronas e paralelas, modo headless robusto e API moderna em Python.
- **FastAPI** gera automaticamente a documentação Swagger/OpenAPI, atendendo ao requisito diferencial do desafio.
- A estrutura modular (`scraper`, `schemas`, `app`) facilita testes isolados e manutenção.
- O scraper simula um navegador real (user-agent, locale, timezone, viewport) para contornar bloqueios de CDN (CloudFront 403).
- Os dados de benefícios são extraídos diretamente das tabelas do accordion na página de perfil, evitando navegação para páginas de detalhe que exigem reCAPTCHA.
- A imagem Docker usa `python:3.13-slim` com instalação do Chromium via `playwright install --with-deps`, resultando na menor imagem viável (~1.1GB com Chromium).
- O CPF é capturado via regex no texto da página (`***.659.347-**`), tornando a extração resiliente a mudanças na estrutura HTML do portal.
- A notificação ao n8n é feita de forma assíncrona após a resposta ser computada, com timeout de 30 segundos para acomodar o payload com screenshot.
