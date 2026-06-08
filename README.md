# Deilify Backend

Repositorio: https://github.com/maocorrea1015/back-deilify

Aviso de licencia: este repositorio incluye software propietario de Infocor. Consulte el archivo [LICENSE](LICENSE) para los términos de uso.

## Descripción
- Backend construido con Flask que expone una API REST.
- Incluye módulos para autenticación, gestión de clientes, facturas, pagos, reportes y componentes de IA.
- Diseñado para ejecutarse en entornos Linux y Windows.

## Estructura principal
- `wsgi.py`: entrada WSGI que crea la aplicación.
- `app/`: paquete principal con configuración, extensiones, API y modelos.
- `requirements.txt`: dependencias del proyecto.
- `migrations/`: scripts de migración de base de datos.
- `tests/`: casos de prueba del backend.

## Requisitos
- Python 3.10+ (se recomienda Python 3.11)
- Virtualenv o entornos equivalentes
- Git

## Configuración en Linux / macOS
1. Clonar el repositorio:

```bash
git clone https://github.com/maocorrea1015/back-deilify.git
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

4. Definir variables de entorno mínimas:

```bash
export SECRET_KEY="cambia-esto"
export FLASK_DEBUG=1
```

5. Ejecutar migraciones si corresponde:

```bash
# alembic upgrade head
```

6. Ejecutar la aplicación en modo desarrollo:

```bash
python wsgi.py
```

## Configuración en Windows (PowerShell)
1. Clonar el repositorio:

```powershell
git clone https://github.com/maocorrea1015/back-deilify.git
cd backend
```

2. Crear y activar entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

4. Definir variables de entorno mínimas:

```powershell
$env:SECRET_KEY = "cambia-esto"
$env:FLASK_DEBUG = "1"
```

5. Ejecutar migraciones si corresponde:

```powershell
# alembic upgrade head
```

6. Ejecutar la aplicación en modo desarrollo:

```powershell
python wsgi.py
```

## Configuración en Windows (CMD)
1. Activar el entorno virtual:

```cmd
venv\Scripts\activate.bat
```

2. Definir variables de entorno:

```cmd
set SECRET_KEY=cambia-esto
set FLASK_DEBUG=1
```

3. Ejecutar la aplicación:

```cmd
python wsgi.py
```

## Ejecución en producción
- Usar un servidor WSGI como `gunicorn` en Linux:

```bash
gunicorn -w 4 wsgi:app
```

En Windows puede utilizarse un servidor compatible con WSGI o una plataforma de despliegue que soporte Flask.

## Pruebas
- Ejecutar los tests disponibles en `tests/`:

```bash
pytest
```

## Licencia
- Este proyecto se distribuye bajo una licencia propietaria de Infocor.
- Consulte [LICENSE](LICENSE) para los términos de uso y restricciones.

## Soporte
- Proyecto interno de Infocor — uso restringido. Para consultas, contacte al equipo responsable de Infocor.
