# utils.py

import datetime

def vigencia_dias(dias: int) -> str:
    """
    Retorna la fecha en formato YYYY-MM-DD sumando días actuales.
    """
    validity = datetime.datetime.now() + datetime.timedelta(days=dias)
    return validity.strftime('%Y-%m-%d')

def mapear_estado_firma(sign_request_state: str) -> str:
    """
    Mapea el estado de una solicitud de firma de Odoo a un código interno.

    Args:
        sign_request_state (str): Estado original de Odoo
            ('shared', 'sent', 'signed', 'canceled', 'expired').
    ODOO Estado (Petición de firma)	Compartido, A firmar, Totalmente firmado, Cancelado, Expirado.

    Returns:
        str: Código de estado interno correspondiente:
            - 'FF' (Firmado)
            - 'OB' (Observado o Cancelado)
            - 'EX' (Expirado)
            - 'EF' (En Firma)
            - 'FT' (En Trámite)
            - 'ND' (No definido)
    """
    mapping = {
        'shared': 'EF',
        'sent': 'FT',
        'signed': 'FF',
        'canceled': 'OB',
        'expired': 'EX',
    }
    return mapping.get(sign_request_state, 'ND')  # ND = No definido
