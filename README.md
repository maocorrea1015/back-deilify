
# Deilify Backend

Repositorio: https://github.com/maocorrea1015/back-deilify

Aviso de licencia: este repositorio incluye software propietario de Infocor. Consulte el archivo [LICENSE](LICENSE) para los términos de uso.

## Descripción

Backend construido con Flask que expone una API REST para el sistema de cartera Deilify.

Incluye módulos para:

* Autenticación y autorización.
* Gestión de clientes.
* Gestión de facturas.
* Gestión de pagos.
* Reportes.
* Integraciones y componentes de IA.

## Flujo de trabajo Git

### Importante

La rama `main` corresponde al entorno de producción.

**No se deben realizar desarrollos, commits o push directamente sobre la rama `main`.**

Todo el trabajo debe realizarse sobre la rama `develop` o sobre ramas derivadas de ella.

### Estructura de ramas

| Rama      | Propósito                |
| --------- | ------------------------ |
| main      | Producción               |
| develop   | Desarrollo e integración |
| feature/* | Nuevas funcionalidades   |
| hotfix/*  | Correcciones urgentes    |

### Clonar la rama de desarrollo

```bash
git clone -b develop --single-branch git@github.com:maocorrea1015/back-deilify.git
cd back-deilify
```

### Actualizar la rama develop

```bash
git checkout develop
git pull origin develop
```

### Crear una rama para una nueva funcionalidad

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-funcionalidad
```

Ejemplo:

```bash
git checkout -b feature/modulo-pagos
```

### Publicar cambios

```bash
git add .
git commit -m "Descripción del cambio"
git push origin feature/nombre-funcionalidad
```

Posteriormente deberá crearse un Pull Request hacia la rama `develop`.

### Restricción

No se aceptarán cambios enviados directamente a `main`.

---

## Estructura principal

* `wsgi.py`: punto de entrada WSGI.
* `app/`: aplicación principal.
* `requirements.txt`: dependencias del proyecto.
* `migrations/`: migraciones de base de datos.
* `tests/`: pruebas automatizadas.

## Requisitos del entorno

El entorno de desarrollo soportado y probado es:

* Python **3.11.9**.
* Git.
* `pip` actualizado.
* Un entorno virtual llamado `.venv`.

No se recomienda utilizar Python 3.10, 3.12, 3.13 o 3.14 para este proyecto, porque las dependencias fijadas en `requirements.txt` fueron validadas con Python 3.11.9.

## Instalación en Windows

Usar PowerShell desde la raíz del repositorio:

```powershell
git clone -b develop --single-branch git@github.com:maocorrea1015/back-deilify.git
Set-Location back-deilify

py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

La salida de `python --version` debe comenzar con `Python 3.11.9`. Si PowerShell bloquea la activación del entorno, ejecutar una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

`nvidia-nccl-cu12` permanece comentada en `requirements.txt` y **no debe instalarse en Windows**.

## Instalación en Linux

Usar Bash desde la raíz del repositorio:

```bash
git clone -b develop --single-branch git@github.com:maocorrea1015/back-deilify.git
cd back-deilify

python3.11 --version
python3.11 -m venv .venv
source .venv/bin/activate

python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

La salida de `python --version` debe ser `Python 3.11.9`. La dependencia `nvidia-nccl-cu12` es opcional y específica de Linux; solo se instala manualmente en Linux cuando el entorno o una integración de GPU la necesita:

```bash
python -m pip install nvidia-nccl-cu12==2.30.4
```

No se debe instalar esta librería en Windows ni macOS. Está comentada en `requirements.txt` para que la instalación estándar sea multiplataforma.

## Variables de entorno

La aplicación usa estas variables:

| Variable | Uso | Valor recomendado |
| --- | --- | --- |
| `SECRET_KEY` | Clave de Flask | Cadena aleatoria de al menos 32 caracteres |
| `JWT_SECRET_KEY` | Firma de tokens JWT | Cadena aleatoria de al menos 32 caracteres |
| `FLASK_DEBUG` | Activa el modo debug | `1` en desarrollo, `0` fuera de desarrollo |
| `SQLALCHEMY_DATABASE_URI` | URL de base de datos | SQLite por defecto |

Windows PowerShell:

```powershell
$env:SECRET_KEY = "clave-local-larga-y-aleatoria"
$env:JWT_SECRET_KEY = "jwt-local-larga-y-aleatoria"
$env:FLASK_DEBUG = "1"
```

Linux:

```bash
export SECRET_KEY="clave-local-larga-y-aleatoria"
export JWT_SECRET_KEY="jwt-local-larga-y-aleatoria"
export FLASK_DEBUG=1
```

La configuración predeterminada utiliza una base SQLite local. Para usar otra base, definir `SQLALCHEMY_DATABASE_URI` antes de iniciar la aplicación.

## Base de datos y migraciones

Aplicar las migraciones desde la raíz del proyecto:

```bash
alembic upgrade head
```

La migración más reciente crea la tabla `acuerdos_pago`, necesaria para Gestión de Cobros / Refinanciación. En desarrollo, `create_app` también crea las tablas que no existen; en entornos compartidos o productivos se debe usar Alembic como fuente de verdad.

Para revisar la versión instalada:

```bash
alembic current
```

## Ejecutar la aplicación

Con `.venv` activado:

```bash
python wsgi.py
```

La API queda disponible normalmente en `http://127.0.0.1:5000`. La documentación interactiva de Flask-RESTX está en `http://127.0.0.1:5000/`.

## API principal

Todas las rutas protegidas requieren `Authorization: Bearer <JWT>`.

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/` | Health check |
| `POST` | `/auth/register` | Registrar usuario |
| `POST` | `/auth/login` | Iniciar sesión |
| `GET` | `/auth/me` | Consultar perfil autenticado |
| `GET` | `/cartera/dashboard` | Métricas de cartera |
| `GET` | `/cartera/facturas` | Listado general de facturas |
| `POST` | `/cartera/facturas` | Sincronizar facturas |
| `GET` | `/cartera/recaudos` | Histórico de pagos de la empresa |
| `POST` | `/cartera/recaudos` | Registrar un pago |
| `GET` | `/cartera/acuerdos-pago` | Listar acuerdos de pago |
| `POST` | `/cartera/acuerdos-pago` | Crear acuerdo de pago |
| `GET` | `/cartera/clientes/{id}/estado-cuenta` | Estado de cuenta de un cliente |
| `GET` | `/clientes/` | Listar clientes |
| `GET` | `/usuarios/` | Listar usuarios |

El listado de facturas acepta `cliente_id` y `estado` (`PENDIENTE`, `PAGADA`, `VENCIDA` o `VIGENTE`). El listado de acuerdos acepta `cliente_id` y `estado` (`ACTIVO`, `CUMPLIDO`, `INCUMPLIDO` o `CANCELADO`). Las consultas se restringen automáticamente a la empresa del token JWT.

## Comandos de cartera

Para marcar como vencidas las facturas pendientes que superaron su fecha de vencimiento:

```bash
flask cartera-cli check-overdue
```

Ejecutar el comando con el entorno `.venv` activado y las mismas variables de entorno de la aplicación.

## Pruebas

El runner estándar no requiere paquetes adicionales:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Para ejecutar únicamente las pruebas de cartera:

```bash
python -m unittest tests.test_cartera -v
```

Si se desea usar `pytest`, instalarlo de forma opcional y ejecutar:

```bash
python -m pip install pytest
python -m pytest
```

Las pruebas de cartera cubren aislamiento multiempresa, facturas, pagos y acuerdos de pago.

## Solución de problemas

* `ModuleNotFoundError`: verificar que `.venv` esté activo y reinstalar con `python -m pip install -r requirements.txt`.
* Versión incorrecta de Python: eliminar `.venv`, instalar Python 3.11.9 y recrearlo con `py -3.11 -m venv .venv` en Windows o `python3.11 -m venv .venv` en Linux.
* Error al instalar `nvidia-nccl-cu12`: omitirla en Windows/macOS; en Linux instalarla manualmente solo si el entorno la requiere.
* Error de tabla inexistente: ejecutar `alembic upgrade head` desde la raíz del repositorio.
* Error de JWT por clave insegura: definir `SECRET_KEY` y `JWT_SECRET_KEY` con cadenas aleatorias de al menos 32 caracteres.

## Producción

La rama `main` contiene exclusivamente versiones aprobadas para producción.

Los despliegues deberán realizarse únicamente a partir de esta rama.

## Licencia

Este proyecto es propiedad exclusiva de Infocor.

Consulte el archivo [LICENSE](LICENSE) para conocer los términos de uso, restricciones y limitaciones de responsabilidad.

## Soporte

Proyecto interno de Infocor.

Para soporte técnico, reporte de errores o solicitudes de acceso, contacte al equipo responsable de Infocor.
