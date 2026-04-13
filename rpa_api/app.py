import os
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from rpa_api.schemas import ConsultaRequest, ConsultaResponse
from rpa_api import scraper

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="RPA Portal da Transparência")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")


@app.post("/api/v1/consulta", response_model=ConsultaResponse)
@limiter.limit("5/minute")
async def consultar(request: Request, body: ConsultaRequest):
    resultado = await scraper.consultar(
        nome=body.nome,
        cpf=body.cpf,
        nis=body.nis,
        filtro_beneficiario=body.filtro_beneficiario,
    )

    if N8N_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(N8N_WEBHOOK_URL, json=resultado.model_dump())
        except Exception:
            pass

    return resultado
