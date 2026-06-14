
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

## Requisitos

* Python 3.10 o superior.
* Git.
* Entorno virtual (venv).

## Configuración en Linux / macOS

### 1. Clonar el repositorio

```bash
git clone -b develop --single-branch git@github.com:maocorrea1015/back-deilify.git
cd back-deilify
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
export SECRET_KEY="cambia-esto"
export FLASK_DEBUG=1
```

### 5. Ejecutar migraciones

```bash
# alembic upgrade head
```

### 6. Ejecutar la aplicación

```bash
python wsgi.py
```

## Configuración en Windows (PowerShell)

### 1. Clonar el repositorio

```powershell
git clone -b develop --single-branch git@github.com:maocorrea1015/back-deilify.git
cd back-deilify
```

### 2. Crear entorno virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```powershell
$env:SECRET_KEY = "cambia-esto"
$env:FLASK_DEBUG = "1"
```

### 5. Ejecutar la aplicación

```powershell
python wsgi.py
```

## Pruebas

Ejecutar todas las pruebas:

```bash
pytest
```

## Producción

La rama `main` contiene exclusivamente versiones aprobadas para producción.

Los despliegues deberán realizarse únicamente a partir de esta rama.

## Licencia

Este proyecto es propiedad exclusiva de Infocor.

Consulte el archivo [LICENSE](LICENSE) para conocer los términos de uso, restricciones y limitaciones de responsabilidad.

## Soporte

Proyecto interno de Infocor.

Para soporte técnico, reporte de errores o solicitudes de acceso, contacte al equipo responsable de Infocor.
