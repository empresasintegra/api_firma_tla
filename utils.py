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
            ('signed', 'refused', 'canceled', 'expired', 'shared', 'sent').

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
        'signed': 'FF',
        'refused': 'OB',
        'canceled': 'OB',
        'expired': 'EX',
        'shared': 'EF',
        'sent': 'FT'
    }
    return mapping.get(sign_request_state, 'ND')  # ND = No definido
