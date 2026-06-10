# Guía de Entorno de Desarrollo Local

Este documento detalla los pasos exactos para levantar el proyecto SkillStat en un entorno local. Sigue las instrucciones en orden.

## 1. Requisitos Previos
* **Python:** Versión 3.13.x o superior.
* **Base de Datos:** PostgreSQL 15.
* **Git:** Para clonar y manejar el flujo de ramas.

## 2. Configuración de la Base de Datos
Antes de ejecutar la aplicación, debes preparar el motor de base de datos local:
1. Abre tu cliente de PostgreSQL (pgAdmin o psql).
2. Crea una base de datos vacía llamada exactamente: `skillstat_dev`.
3. Asegúrate de tener a la mano tu usuario (ej. `postgres`) y contraseña locales.

## 3. Entorno Virtual y Dependencias
Posiciónate en la raíz del proyecto y ejecuta:

```bash
# Entrar al directorio del backend
cd backend

# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate

# Instalar dependencias base y de desarrollo
pip install -r requirements.txt
pip install -r requirements-dev.txt

```

## 4. Variables de Entorno

Crea un archivo llamado `.env` dentro de la carpeta `backend/` y define estrictamente las siguientes variables:

```env
FLASK_APP=app
FLASK_ENV=development
# Reemplaza 'tu_usuario' y 'tu_contraseña' con tus credenciales locales de Postgres:
DATABASE_URL=postgresql://tu_usuario:tu_contraseña@localhost:5432/skillstat_dev

```

*Nota:* El archivo `.env` está ignorado por Git por razones de seguridad. Nunca lo subas al repositorio.

## 5. Migraciones (Alembic)

Para que las tablas físicas de la base de datos se alineen con los modelos de SQLAlchemy, ejecuta:

```bash
# Estando dentro de la carpeta backend/ y con el .venv activado:
flask db upgrade

```

*Esto aplicará el historial de migraciones y construirá las tablas respetando la 3FN.*

## 6. Ejecución del Servidor

Finalmente, levanta el servicio con:

```bash
flask run

```

El backend estará disponible en `http://127.0.0.1:5000`.
