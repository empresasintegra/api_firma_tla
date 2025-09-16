# main.py

from fastapi import FastAPI, HTTPException, Query
from models import FirmaRequest
from connection import (procesar_solicitud_firma, obtener_info_firma, obtener_rol_por_id, obtener_tag_por_id, editar_tag,
                        cancelar_documento_firma, obtener_sign_request, traer_documentos_firmados, notificar_firma)
from utils import mapear_estado_firma

app = FastAPI()

@app.post("/conexion")
def solicitud_firma(data: FirmaRequest):
    """
    Endpoint principal para enviar una solicitud de firma a Odoo.

    Args:
        data (FirmaRequest): Objeto con la información necesaria para generar la solicitud de firma.

    Returns:
        dict: Resultado de la operación, usualmente con el ID de la solicitud.
    """
    try:
        return procesar_solicitud_firma(data)
    except Exception as e:
        print("❌ Error interno:", e)  # Esto imprime el error exacto
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recuperacion_manual")
def recuperacion_manual(id: int = Query(..., description="ID de la firma a recuperar manualmente")):
    """
    Recupera manualmente una solicitud de firma y notifica su estado.
    """
    try:
        sign_request = obtener_sign_request(id)
        estado = mapear_estado_firma(sign_request['state'])

        documentos = traer_documentos_firmados(id) if estado == 'FF' else {}

        payload = {
            "tag": "tag",
            "estado_firma": estado,
            "odoo_id": id,
            "documento_pdf": documentos.get("documento"),
            "certificado_pdf": documentos.get("certificado"),
        }

        notificar_firma(payload)
        return {"message": "Recuperación manual procesada exitosamente."}

    except Exception as e:
        import logging
        logging.error(f"❌ Error en /recuperacion_manual: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar la recuperación manual.")


@app.post("/recuperacion_webhook")
def recuperacion_webhook(id: int = Query(..., description="ID de la firma a recuperar por webhook")):
    """
    Recupera una solicitud de firma activada por webhook y notifica su estado.
    """
    try:
        sign_request = obtener_sign_request(id)
        estado = mapear_estado_firma(sign_request['state'])

        documentos = traer_documentos_firmados(id)

        payload = {
            "tag": "tag",
            "estado_firma": estado,
            "odoo_id": id,
            "documento_pdf": documentos.get("documento"),
            "certificado_pdf": documentos.get("certificado"),
        }

        notificar_firma(payload)
        return {"message": "Recuperación webhook procesada exitosamente."}

    except Exception as e:
        import logging
        logging.error(f"❌ Error en /recuperacion_webhook: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar la recuperación por webhook.")


@app.put("/cancelar")
def cancelar_firma(id: int = Query(...)):
    """
    Cancela una solicitud de firma en Odoo, si aún no ha sido firmada o cancelada.

    Args:
        id (int): ID de la solicitud de firma a cancelar.

    Returns:
        dict: Mensaje indicando el resultado de la operación.

    Raises:
        HTTPException: Si ocurre un error al intentar cancelar la solicitud.
    """
    try:
        return cancelar_documento_firma(id)
    except Exception as e:
        print("❌ Error en /cancelar:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
def info(id: int = Query(..., description="ID de la solicitud de firma en Odoo")):
    """
    Devuelve la información detallada de una solicitud de firma desde Odoo.

    Args:
        id (int): ID de la solicitud de firma (sign.request).

    Returns:
        dict: Datos del documento encontrado o error si no existe.
    """
    try:
        return obtener_info_firma(id)
    except Exception as e:
        print("❌ Error en /info:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/roles")
def roles(id: int = Query(..., description="ID del rol de firma")):
    """
    Devuelve la información de un rol de firma (sign.item.role).
    """
    try:
        return obtener_rol_por_id(id)
    except Exception as e:
        print("❌ Error en /roles:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tags")
def tags(id: int = Query(..., description="ID de la etiqueta de plantilla")):
    """
    Devuelve la información de una etiqueta de plantilla (sign.template.tag).
    """
    try:
        return obtener_tag_por_id(id)
    except Exception as e:
        print("❌ Error en /tags:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/edit_tag")
def edit_tag(id: int = Query(...), nuevo_nombre: str = Query(...)):
    """
    Edita el nombre de una etiqueta de plantilla de firma en Odoo.

    Args:
        id (int): ID de la etiqueta a editar.
        nuevo_nombre (str): Nuevo nombre para la etiqueta.

    Returns:
        dict: Mensaje indicando si la edición fue exitosa.

    Raises:
        HTTPException: Si ocurre un error en la actualización del nombre.
    """
    try:
        return editar_tag(id, nuevo_nombre)
    except Exception as e:
        print("❌ Error en /edit_tag:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/estados_firma_odoo")
def estados_firma_odoo(sign_request_state: str):
    """
    Traduce el estado de una solicitud de firma de Odoo a un código interno.

    Args:
        sign_request_state (str): Estado original de la solicitud en Odoo.

    Returns:
        dict: Código de estado interno según la lógica de negocio.

    Raises:
        HTTPException: Si ocurre un error en el mapeo del estado.
    """
    try:
        estado = mapear_estado_firma(sign_request_state)
        return {"estado": estado}
    except Exception as e:
        print("❌ Error en /estados_firma_odoo:", e)
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/extra")
# def extra(id):
#     """ Endpoint de prueba para obtener datos adicionales desde Odoo. """
#     from xmlrpc.client import ServerProxy
#     try:
#         db='develop'
#         password='d5kSw]+"Q"31Jdev'
#         url='https://develop.odoo.com/'
#         username='desarrollo_firma@empresasintegra.cl'
#         # Autenticación en Odoo
#         uid = authenticate()
#         if uid:
#             models = ServerProxy('{}/xmlrpc/2/object'.format(url))
#             test = models.execute_kw(
#                 db, uid, password,
#                 'ir.attachment', 'search_read',
#                 [[('res_id', '=', id)]],
#                 {'fields': [
#                     'access_token', 'checksum', 'company_id', 'create_date', 'create_uid', 'datas', 'db_datas', 'description', 'display_name', 'file_size', 'id', 'image_height', 'image_src', 'image_width', 'index_content', 'local_url', 'mimetype', 'name', 'original_id', 'public', 'res_field', 'res_id', 'res_model', 'res_name', 'store_fname', 'type', 'url', 'voice_ids', 'write_date', 'write_uid'
#                 ]}  # campos seguros
#             )
#             # tag_mapping = {tag['name']: tag['id'] for tag in test}
#             # print('tag_mapping', tag_mapping)

#             return test

#     except Exception as e:
#         print(e)
