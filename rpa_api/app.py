from fastapi import FastAPI
from rpa_api.schemas import ConsultaRequest, ConsultaResponse
from rpa_api import scraper

app = FastAPI(title="RPA Portal da Transparência")


@app.post("/api/v1/consulta", response_model=ConsultaResponse)
async def consultar(request: ConsultaRequest):
    resultado = await scraper.consultar(
        nome=request.nome,
        cpf=request.cpf,
        nis=request.nis,
        filtro_beneficiario=request.filtro_beneficiario,
    )
    return resultado
