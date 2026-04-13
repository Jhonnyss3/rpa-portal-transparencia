import base64
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

BASE_URL = "https://www.portaldatransparencia.gov.br"
BUSCA_URL = f"{BASE_URL}/pessoa-fisica/busca/lista"


async def _screenshot_base64(page: Page) -> str:
    dados = await page.screenshot(full_page=True)
    return base64.b64encode(dados).decode("utf-8")


async def _coletar_beneficios_do_perfil(page: Page) -> list:
    """Extrai dados dos benefícios diretamente das tabelas do accordion no perfil."""
    beneficios = []

    # Cada bloco de benefício tem um <strong> com o nome e uma <table> com os dados
    blocos = await page.query_selector_all("#accordion-recebimentos-recursos .br-table")

    for bloco in blocos:
        # Nome do benefício vem do <strong> antes da tabela
        strong = await bloco.query_selector("strong")
        tipo = (await strong.inner_text()).strip() if strong else "desconhecido"

        # Coleta cabeçalhos
        headers = []
        ths = await bloco.query_selector_all("thead th")
        for th in ths:
            texto = (await th.inner_text()).strip()
            if texto and texto.lower() != "detalhar":
                headers.append(texto)

        # Coleta linhas
        registros = []
        trs = await bloco.query_selector_all("tbody tr")
        for tr in trs:
            tds = await tr.query_selector_all("td:not(.noprint)")
            valores = [(await td.inner_text()).strip() for td in tds]
            if valores:
                registros.append(dict(zip(headers, valores)))

        beneficios.append({"tipo": tipo, "dados": registros})

    return beneficios


async def consultar(
    nome: str | None,
    cpf: str | None,
    nis: str | None,
    filtro_beneficiario: bool,
) -> dict:
    termo = cpf or nis or nome

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={"Accept-Language": "pt-BR,pt;q=0.9"},
        )
        page = await context.new_page()

        try:
            # Monta URL de busca
            url_busca = f"{BUSCA_URL}?termo={termo}"
            if filtro_beneficiario:
                url_busca += "&filtros=beneficiarioProgramaSocial:1"

            await page.goto(url_busca, wait_until="networkidle")

            # Aguarda resultados ou mensagem de não encontrado
            try:
                await page.wait_for_selector(".link-busca-nome, .br-item.not-found", timeout=15000)
            except PlaywrightTimeout:
                return {
                    "status": "erro",
                    "mensagem": "Não foi possível retornar os dados no tempo de resposta solicitado",
                }

            # Verifica se não encontrou resultados
            not_found = await page.query_selector(".br-item.not-found")
            if not_found:
                return {
                    "status": "erro",
                    "mensagem": f"Foram encontrados 0 resultados para o termo {termo}",
                }

            # Pega o primeiro resultado
            primeiro = await page.query_selector(".link-busca-nome")
            nome_encontrado = (await primeiro.inner_text()).strip()
            href = await primeiro.get_attribute("href")

            # Navega para o perfil da pessoa
            url_perfil = href if href.startswith("http") else f"{BASE_URL}{href}"
            await page.goto(url_perfil, wait_until="networkidle")

            try:
                await page.wait_for_selector("main", timeout=15000)
            except PlaywrightTimeout:
                return {
                    "status": "erro",
                    "mensagem": "Não foi possível retornar os dados no tempo de resposta solicitado",
                }

            # Dispensa cookie banner se presente
            try:
                btn_cookie = await page.query_selector(
                    "button:has-text('Rejeitar cookies opcionais'), button:has-text('Aceitar todos')"
                )
                if btn_cookie:
                    await btn_cookie.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # Captura CPF exibido na página
            cpf_encontrado = None
            try:
                el = await page.query_selector("[data-cpf], .cpf, #cpf")
                if el:
                    cpf_encontrado = (await el.inner_text()).strip()
            except Exception:
                pass

            # Expande todas as seções do accordion
            try:
                secoes = await page.query_selector_all(".br-accordion button.header")
                for secao in secoes:
                    await secao.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            await page.wait_for_timeout(1000)

            # Screenshot da tela de panorama
            screenshot = await _screenshot_base64(page)

            # Coleta benefícios direto das tabelas do accordion
            beneficios = await _coletar_beneficios_do_perfil(page)

            return {
                "status": "sucesso",
                "nome": nome_encontrado,
                "cpf": cpf_encontrado,
                "beneficios": beneficios,
                "screenshot_base64": screenshot,
                "mensagem": None,
            }

        except PlaywrightTimeout:
            return {
                "status": "erro",
                "mensagem": "Não foi possível retornar os dados no tempo de resposta solicitado",
            }
        finally:
            await browser.close()
