# Deilify Backend

Aviso de licencia: este repositorio incluye software propietario de Infocor. Consulte el archivo [LICENSE](LICENSE) para los términos de uso.

**Descripción**
- Proyecto backend construido con Flask que expone una API REST (flask-restx).
- Contiene módulos para autenticación, gestión de clientes, facturas, pagos, reportes y componentes de IA.

**Estructura principal**
- `wsgi.py`: entrada WSGI que crea la aplicación.
- `app/`: paquete principal con configuración, extensiones, API y modelos.
- `requirements.txt`: dependencias del proyecto.
- `migrations/`: scripts de migración de base de datos (Alembic).

**Requisitos**
- Python 3.10+ (se recomienda 3.11)
- Virtualenv (o equivalente)

**Clonar y poner en marcha (rápido)**
1. Clonar el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd backend
```

2. Crear y activar entorno virtual:

```bash
python -m venv venv
source venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Variables de entorno mínimas (ejemplo):

```bash
export SECRET_KEY="cambia-esto"
export FLASK_DEBUG=1   # opcional durante desarrollo
```

5. Migraciones (si aplica):

```bash
# ejecutar las migraciones si usa Alembic/SQLAlchemy
# alembic upgrade head
```

6. Ejecutar la aplicación (modo desarrollo):

```bash
python wsgi.py
```

La API inicial se encuentra en la ruta raíz (`/`) y devuelve un chequeo de salud.

**Ejecución en producción**
- Usar un servidor WSGI como `gunicorn`: `gunicorn -w 4 wsgi:app`.

**Pruebas**
- Si hay tests en `tests/`, ejecutar: `pytest` (instale `pytest` si falta).

**Contacto / Soporte**
- Proyecto interno de Infocor — uso restringido. Para dudas, contacte al equipo responsable de Infocor.

---
Actualizado por Infocor: licencia propietaria incluida en [LICENSE](LICENSE).
