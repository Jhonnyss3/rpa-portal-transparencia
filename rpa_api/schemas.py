from pydantic import BaseModel, model_validator
from typing import Optional


class ConsultaRequest(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    nis: Optional[str] = None
    filtro_beneficiario: bool = False

    @model_validator(mode="after")
    def ao_menos_um_campo(self):
        if not any([self.nome, self.cpf, self.nis]):
            raise ValueError("Informe ao menos um dos campos: nome, cpf ou nis")
        return self


class BeneficioDetalhe(BaseModel):
    tipo: str
    dados: list[dict]


class ConsultaResponse(BaseModel):
    status: str
    nome: Optional[str] = None
    cpf: Optional[str] = None
    beneficios: list[BeneficioDetalhe] = []
    screenshot_base64: Optional[str] = None
    mensagem: Optional[str] = None
