from pydantic import BaseModel
from typing import List, Optional

class SigningParty(BaseModel):
    """
    Representa a una persona o entidad que debe firmar el documento.
    """
    name: str
    vat: str
    email: str
    display_name: str

class FirmaRequest(BaseModel):
    """
    Estructura de los datos necesarios para crear una solicitud de firma en Odoo.
    """
    SigningParties: List[SigningParty]
    document: str  # PDF codificado en base64
    reference: str
    reminder: Optional[int] = "1" # True
    message: Optional[str] = ""
    subject: str
    pages: List[int]
    tag: str
