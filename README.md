# 📬 API de Firma Electrónica con FastAPI y Odoo

Este proyecto es una API REST construida con **FastAPI** para enviar documentos a firmar mediante **Odoo** usando XML-RPC.

---

<!-- ## 📁 Estructura del Proyecto

api_firma_tla/
├── main.py                          # Punto de entrada de FastAPI
├── connection.py                    # Lógica de conexión y negocio con Odoo
├── models.py                        # Esquemas de datos Pydantic
├── utils.py
├── config.py                        # Carga de variables de entorno y configuración general
├── Dockerfile
├── docker-compose.yml
├── .env
├── requirements.txt
└── README.md                        # Documentación del proyecto -->


---

## ⚙️ Requisitos

- Python 3.11+
- Docker
- Acceso a una instancia de Odoo (con módulo de firma electrónica habilitado)

---

## 🧪 Instalación y Ejecución

1. Clona el repositorio:

```bash
git clone https://github.com/tuusuario/api_firma_tla.git
cd api_firma_tla
```

2. Crea el archivo .env con tus credenciales de Odoo:

<!-- ODOO_URL=http://localhost:8069
ODOO_DB=nombre_de_base
ODOO_USERNAME=usuario@empresa.com
ODOO_PASSWORD=tu_contraseña
URL_NOTIFICACIONES=https://midominio.com/notificaciones -->


3. Ejecuta el servidor:

`docker-compose up --build`

Accede a la API en http://localhost:8000


4. Visita la documentación automática (Swagger UI)

Una vez en ejecución, puedes ver la documentación interactiva en:

http://localhost:8000/docs

http://localhost:8000/redoc


Envía una solicitud de firma a Odoo.

## 📝 Ejemplo de cuerpo (JSON):
```bash
{
  "SigningParties": [
    {
      "name": "Juan Pérez",
      "vat": "12345678-9",
      "email": "juan@example.com",
      "display_name": "Trabajador"
    },
    {
      "name": "Empresa S.A.",
      "vat": "98765432-1",
      "email": "firma@empresa.com",
      "display_name": "Empleador"
    }
  ],
  "document": "BASE64_DEL_PDF",
  "reference": "Contrato001",
  "reminder": "1", # True
  "message": "Por favor firmar lo antes posible.",
  "subject": "Contrato de Trabajo",
  "pages": [1],
  "tag": "tla"
}

🔁 Respuesta esperada:
{
  "status": "success",
  "request_id": 123
}
```

