# connection.py

import os
import json
import logging
from config import settings
from xmlrpc.client import ServerProxy
from models import FirmaRequest
from utils import vigencia_dias

db = settings.ODOO_DB
url = settings.ODOO_URL
username = settings.ODOO_USERNAME
password = settings.ODOO_PASSWORD
url_notificaciones = settings.URL_NOTIFICACIONES

def authenticate():
    """
    Se autentica contra el servidor Odoo usando las credenciales del .env.

    Returns:
        int: UID del usuario autenticado.

    Raises:
        Exception: Si falla la autenticación.
    """
    common = ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise Exception("Fallo de autenticación con Odoo")
    return uid # Devuelve el uid

def create_partners(signing_parties, uid, password, models):
    """
    Crea o actualiza los partners (firmantes) en Odoo usando el RUT (vat) como identificador único.

    Args:
        signing_parties (List[SigningParty]): Lista de firmantes.
        uid (int): UID autenticado.
        password (str): Contraseña del usuario.
        models: Objeto de conexión XML-RPC.

    Returns:
        List[int]: IDs de los partners en Odoo.
    """
    partners = []

    for party in signing_parties:
        data_to_write = party.model_dump()
        rut = data_to_write.get('vat')

        if not rut:
            raise ValueError("Cada firmante debe tener un RUT (campo 'vat').")

        # Buscar por vat (RUT)
        existing = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[('vat', '=', rut)]],
            {'fields': ['id', 'name', 'email', 'display_name', 'vat'], 'limit': 1}
        )

        if not existing:
            # Crear si no existe
            partner_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [data_to_write])
        else:
            # Si existe, verificar si hay cambios
            partner = existing[0]
            changes = {}

            for field in ['name', 'email', 'display_name', 'vat']:
                new_value = data_to_write.get(field)
                if new_value and new_value != partner.get(field):
                    changes[field] = new_value

            if changes:
                models.execute_kw(
                    db, uid, password,
                    'res.partner', 'write',
                    [[partner['id']], changes]
                )

            partner_id = partner['id']

        partners.append(partner_id)

    return partners

def create_tag(tag, uid, password, models):
    """
    Crea una etiqueta para el template si no existe.

    Args:
        tag (str): Nombre de la etiqueta.
        uid (int): UID autenticado.
        password (str): Contraseña.
        models: Conexión XML-RPC.

    Returns:
        int: ID de la etiqueta en Odoo.
    """
    existing = models.execute_kw(db, uid, password, 'sign.template.tag', 'search', [[('name', '=', tag)]])
    if not existing:
        tag_id = models.execute_kw(db, uid, password, 'sign.template.tag', 'create', [{'name': tag}])
    else:
        tag_id = existing[0]
    return tag_id

def create_attachment(document_base64, uid, password, models):
    """
    Crea un attachment en Odoo a partir de un documento codificado en base64.

    Args:
        document_base64 (str): Documento PDF codificado en base64.
        uid (int): UID autenticado.
        password (str): Contraseña.
        models: Conexión XML-RPC.

    Returns:
        int: ID del attachment.
    """
    attachment = {
        'name': 'documento_firma.pdf',
        'datas': document_base64,
        'type': 'binary',
        'res_model': 'sign.template'
    }
    return models.execute_kw(db, uid, password, 'ir.attachment', 'create', [attachment])

def create_template(subject, attachment_id, signing_parties, pages,
                    trabajador_role_id, empleador_role_id,
                    tag_id, uid, password, models):
    """
    Crea un template de firma en Odoo con posiciones definidas según el firmante.

    Args:
        subject (str): Asunto del documento.
        attachment_id (int): ID del PDF en Odoo.
        signing_parties (List[SignParty]): Lista de firmantes.
        pages (List[int]): Páginas donde colocar firmas.
        *_role_id (int): ID de los roles de Odoo.
        tag_id (int): ID de la etiqueta de plantilla.
        uid (int): UID autenticado en Odoo.
        password (str): Contraseña del usuario.
        models: Proxy XML-RPC para 'object'.

    Returns:
        int: ID del template creado.
    """

    # Posiciones por rol
    layout_roles = {
        "Trabajador": {
            "posX": 0.10,
            "firmaY": 0.75,
            "nombreY": 0.85,
            "rutY": 0.865
        },
        "Empleador": {
            "posX": 0.65,
            "firmaY": 0.75,
            "nombreY": 0.85,
            "rutY": 0.865
        }
    }

    # Mapping de roles
    role_mapping = {
        "Trabajador": trabajador_role_id,
        "Empleador": empleador_role_id
    }

    template_data = {
        'name': subject,
        'attachment_id': attachment_id,
        'sign_item_ids': [],
        'tag_ids': [(6, 0, [tag_id])]
    }

    for signer in signing_parties:
        # display_name = signer['display_name']
        display_name = signer.display_name
        layout = layout_roles.get(display_name)
        role_id = role_mapping.get(display_name)

        if not layout or not role_id:
            continue  # Skip si no hay datos

        for page in pages:
            # Campo Firma
            template_data['sign_item_ids'].append(
                (0, 0, {
                    'type_id': 1,  # Firma
                    'required': True,
                    'name': signer.name,
                    'page': page,
                    'responsible_id': role_id,
                    'posX': layout['posX'],
                    'posY': layout['firmaY'],
                    'width': 0.2,
                    'height': 0.1,
                })
            )
            # Campo Nombre
            template_data['sign_item_ids'].append(
                (0, 0, {
                    'type_id': 3,  # Nombre
                    'required': True,
                    'name': signer.name,
                    'page': page,
                    'responsible_id': role_id,
                    'posX': layout['posX'],
                    'posY': layout['nombreY'],
                    'width': 0.2,
                    'height': 0.015,
                })
            )
            # Campo RUT
            template_data['sign_item_ids'].append(
                (0, 0, {
                    'type_id': 12,  # RUT
                    'required': True,
                    'name': signer.vat,
                    'page': page,
                    'responsible_id': role_id,
                    'posX': layout['posX'],
                    'posY': layout['rutY'],
                    'width': 0.2,
                    'height': 0.015,
                })
            )

    # Crear template en Odoo
    template_id = models.execute_kw(
        db, uid, password, 'sign.template', 'create', [template_data]
    )

    return template_id

def create_signature_request(template_id, subject, reference, reminder, partner_ids, trabajador_role_id, empleador_role_id, tag, message, uid, password, models):
    """
    Crea una solicitud de firma basada en un template, firmantes y tipo de documento.

    [Parámetros omitidos por brevedad]

    Returns:
        int: ID de la solicitud de firma.
    """
    validity = vigencia_dias(8)
    role_ids = [trabajador_role_id, empleador_role_id]

    request_items = [
        (0, 0, {'partner_id': partner_ids[i], 'role_id': role_ids[i], 'mail_sent_order': i + 1})
        for i in range(2)
    ]

    data = {
        'template_id': template_id,
        'subject': subject,
        'reference': reference,
        'reminder_enabled': True,
        'reminder': reminder,
        'validity': validity,
        'request_item_ids': request_items,
        'message': message,
        'state': 'sent'
    }

    return models.execute_kw(db, uid, password, 'sign.request', 'create', [data])

def procesar_solicitud_firma(data: FirmaRequest):
    """
    Orquesta todo el proceso: autenticación, creación de partners, template y solicitud de firma.

    Args:
        data (FirmaRequest): Información de la solicitud enviada desde el frontend/API.

    Returns:
        dict: Respuesta con el ID del request o error.
    """
    uid = authenticate()
    models = ServerProxy(f"{url}/xmlrpc/2/object")

    # Obtener roles
    roles = models.execute_kw(db, uid, password, 'sign.item.role', 'search_read', [[]], {'fields': ['id', 'name']})
    role_map = {r['name']: r['id'] for r in roles}

    trabajador_role_id = role_map.get('Employee') # Trabajador
    empleador_role_id = role_map.get('User') # Empresa

    partner_ids = create_partners(data.SigningParties, uid, password, models)
    tag_id = create_tag(data.tag, uid, password, models)
    attachment_id = create_attachment(data.document, uid, password, models)

    template_id = create_template(data.subject, attachment_id, data.SigningParties, data.pages,
                                      trabajador_role_id, empleador_role_id, tag_id,
                                      uid, password, models)
    request_id = create_signature_request(template_id, data.subject, data.reference, data.reminder,
                                              partner_ids, trabajador_role_id, empleador_role_id,
                                              data.tag, data.message, uid, password, models)

    return {"status": "success", "request_id": request_id}


def obtener_sign_request(id: int):
    """
    Obtiene información de la solicitud de firma desde Odoo.

    Args:
        id (int): ID de la solicitud de firma.

    Returns:
        dict: Diccionario con 'state' y 'reference'.
    """
    uid = authenticate()
    models = ServerProxy(f'{url}/xmlrpc/2/object')

    result = models.execute_kw(
        db, uid, password,
        'sign.request', 'search_read',
        [[('id', '=', id)]],
        {'fields': ['state', 'reference']}
    )

    if not result:
        raise ValueError(f"No se encontró la solicitud con ID {id}")

    return result[0]


def traer_documentos_firmados(id: int) -> dict:
    """
    Obtiene los documentos firmados desde Odoo, en base64.

    Args:
        id (int): ID de la solicitud de firma.

    Returns:
        dict: Diccionario con 'documento' y 'certificado' en base64.
    """
    uid = authenticate()
    models = ServerProxy(f'{url}/xmlrpc/2/object')

    sign_request = models.execute_kw(
        db, uid, password,
        'sign.request', 'search_read',
        [[('id', '=', id)]],
        {'fields': ['completed_document_attachment_ids']}
    )

    if not sign_request or not sign_request[0]['completed_document_attachment_ids']:
        return {}

    attachment_ids = sign_request[0]['completed_document_attachment_ids']
    documentos = models.execute_kw(
        db, uid, password,
        'ir.attachment', 'search_read',
        [[('id', 'in', attachment_ids)]],
        {'fields': ['name', 'datas']}
    )

    resultado = {"documento": None, "certificado": None}

    
    for doc in documentos:
        if 'certificado' in doc['name'].lower():
            resultado["certificado"] = doc['datas']
        else:
            resultado["documento"] = doc['datas']

    return resultado


def notificar_firma(payload: dict):
     """
     Envía una notificación HTTP con los datos de la firma.

     Args:
         payload (dict): Datos a enviar en la notificación.

     Returns:
         str: Mensaje de éxito o lanza error.
     """
     import requests

     headers = {'Content-Type': 'application/json'}
     response = requests.post(url_notificaciones, headers=headers, data=json.dumps(payload))
     response.raise_for_status()
     return "Notificación enviada exitosamente"


def cancelar_documento_firma(doc_id: int):
    """
    Cancela un documento de solicitud de firma (sign.request) en Odoo,
    si su estado actual lo permite.

    Args:
        doc_id (int): ID del documento de firma a cancelar.

    Returns:
        dict: Mensaje indicando el resultado de la operación.

    Raises:
        ValueError: Si no se encuentra el documento con el ID proporcionado.
        Exception: Para otros errores generales de conexión o ejecución.
    """
    uid = authenticate()
    models = ServerProxy(f'{url}/xmlrpc/2/object')

    documento = models.execute_kw(
        db, uid, password,
        'sign.request', 'search_read',
        [[('id', '=', doc_id)]],
        {'fields': ['id', 'state']}
    )

    if not documento:
        raise ValueError("No se encontró el documento con el ID proporcionado.")

    estado = documento[0]['state']

    if estado == 'canceled':
        return {"message": "El documento ya está cancelado."}
    elif estado == 'signed':
        return {"message": "El documento está firmado."}

    models.execute_kw(
        db, uid, password,
        'sign.request', 'write',
        [doc_id, {'state': 'canceled'}]
    )

    return {"message": "El documento se ha cancelado exitosamente."}


def obtener_info_firma(request_id: int):
    """
    Obtiene la información detallada de una solicitud de firma (sign.request) y su primer firmante.

    Args:
        request_id (int): ID de la solicitud de firma en Odoo.

    Returns:
        dict: Datos del documento y estado del firmante.
    """
    uid = authenticate()
    models = ServerProxy(f'{url}/xmlrpc/2/object')

    # Buscar documento
    documento = models.execute_kw(
        db, uid, password,
        'sign.request', 'search_read',
        [[('id', '=', request_id)]],
        {'fields': [
            'id', 'reference', 'subject', 'state', 'validity',
            'request_item_ids', 'create_date', 'completion_date',
            'message', 'template_id', 'access_token'
        ]}
    )

    if not documento:
        raise ValueError(f"No se encontró ningún documento con ID {request_id}")

    # Obtener estado del primer firmante (opcional)
    firma_estado = None
    if documento[0]['request_item_ids']:
        firma_id = documento[0]['request_item_ids'][0]
        firma = models.execute_kw(
            db, uid, password,
            'sign.request.item', 'search_read',
            [[('id', '=', firma_id)]],
            {'fields': ['state']}
        )
        if firma:
            firma_estado = firma[0]['state']

    # Agregar el estado del firmante si existe
    documento[0]['firma_estado'] = firma_estado

    return documento[0]


def obtener_rol_por_id(role_id: int):
    """
    Obtiene la información de un rol de firma desde Odoo.

    Args:
        role_id (int): ID del rol.

    Returns:
        dict: Datos del rol encontrado.
    """
    uid = authenticate()
    models = ServerProxy(f'{url}/xmlrpc/2/object')

    roles = models.execute_kw(
        db, uid, password,
        'sign.item.role', 'search_read',
        [[('id', '=', role_id)]],
        {'fields': ['id', 'name']}
    )

    if not roles:
        raise ValueError(f"No se encontró ningún rol con ID {role_id}")

    return roles[0]


def obtener_tag_por_id(tag_id: int):
    """
    Obtiene la información de una etiqueta de plantilla desde Odoo.

    Args:
        tag_id (int): ID de la etiqueta.

    Returns:
        dict: Datos de la etiqueta encontrada.
    """
    uid = authenticate()
    models = ServerProxy(f'{url}/xmlrpc/2/object')

    tags = models.execute_kw(
        db, uid, password,
        'sign.template.tag', 'search_read',
        [[('id', '=', tag_id)]],
        {'fields': ['id', 'name', 'display_name']}
    )

    if not tags:
        raise ValueError(f"No se encontró ninguna etiqueta con ID {tag_id}")

    return tags[0]


def editar_tag(tag_id: int, nuevo_nombre: str):
    """
    Edita el nombre de una etiqueta de firma (sign.template.tag) en Odoo.

    Args:
        tag_id (int): ID de la etiqueta a editar.
        nuevo_nombre (str): Nuevo valor para el campo 'name' de la etiqueta.

    Returns:
        dict: Mensaje indicando si la actualización fue exitosa o no.

    Raises:
        ValueError: Si no se encuentra la etiqueta con el ID proporcionado.
        Exception: Para otros errores generales de conexión o ejecución.
    """
    uid = authenticate()
    models = ServerProxy(f'{url}/xmlrpc/2/object')

    tag = models.execute_kw(
        db, uid, password,
        'sign.template.tag', 'search_read',
        [[('id', '=', tag_id)]],
        {'fields': ['id', 'name', 'display_name']}
    )

    if not tag:
        raise ValueError("No se encontró el ID proporcionado.")

    models.execute_kw(
        db, uid, password,
        'sign.template.tag', 'write',
        [tag_id, {'name': nuevo_nombre}]
    )

    return {"message": "El tag se ha actualizado exitosamente."}
