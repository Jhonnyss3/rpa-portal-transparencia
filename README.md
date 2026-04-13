# RPA Portal da Transparência — API

API desenvolvida em Python com FastAPI para automação de consultas ao [Portal da Transparência do Governo Federal](https://portaldatransparencia.gov.br/), coletando dados de pessoas físicas e seus vínculos com programas sociais.

## Tecnologias

- **Python 3.13**
- **FastAPI** — framework web e documentação automática (Swagger/OpenAPI)
- **Playwright** — automação headless do navegador
- **Poetry** — gerenciamento de dependências

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

## Instalação

**Pré-requisitos:** Python 3.13+ e Poetry instalados.

```bash
# Instalar dependências
poetry install

# Instalar o navegador do Playwright
poetry run playwright install chromium
```

## Rodando a aplicação

```bash
poetry run fastapi dev rpa_api/app.py
```

Acesse:
- API: `http://127.0.0.1:8000`
- Documentação Swagger: `http://127.0.0.1:8000/docs`
- Documentação ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### `POST /api/v1/consulta`

Inicia a automação e retorna os dados coletados do Portal da Transparência.

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
  "cpf": "***.***.***-**",
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

## Decisões Técnicas

- **Playwright** foi escolhido por oferecer suporte nativo a execuções assíncronas e paralelas, modo headless robusto e API moderna em Python.
- **FastAPI** gera automaticamente a documentação Swagger/OpenAPI, atendendo ao requisito diferencial do desafio.
- A estrutura modular (`scraper`, `schemas`, `app`) facilita testes isolados e manutenção.
- O scraper simula um navegador real (user-agent, locale, timezone, viewport) para contornar bloqueios de CDN (CloudFront 403).
- Os dados de benefícios são extraídos diretamente das tabelas do accordion na página de perfil, evitando navegação para páginas de detalhe que exigem reCAPTCHA.
