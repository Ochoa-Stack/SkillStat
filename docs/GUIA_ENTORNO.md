# Configuracion del entorno local

Esta guia explica como preparar la maquina para trabajar en SkillStat desde cero. La seguimos la primera vez que clonamos el repositorio y cada vez que alguien nuevo se integra al equipo.

## Lo que necesitamos tener instalado

- **Python 3.13.x** - lo descargamos desde https://www.python.org/downloads/
  Verificamos la instalacion con: `python --version`
- **Git** - lo descargamos desde https://git-scm.com/
  Verificamos con: `git --version`
- **PostgreSQL 15** - lo descargamos desde https://www.postgresql.org/download/
  Durante la instalacion en Windows, el instalador nos deja definir la contraseña del usuario `postgres` y el puerto (dejamos el 5432 por defecto salvo que ya tengamos algo corriendo ahi). Verificamos con:
  `psql --version`
  Es importante que durante la instalacion se incluyan las "Command Line Tools" (vienen marcadas por defecto). De ahi salen `pg_dump` y `pg_restore`, que el proyecto usa para generar y restaurar respaldos de la base de datos. Si en algun punto un comando `pg_dump` o `pg_restore` no se reconoce en la terminal, lo mas probable es que la carpeta `bin` de la instalacion de PostgreSQL no este en el PATH del sistema.
- Un editor de codigo. Recomendamos Visual Studio Code.

## Pasos para configurar el proyecto

**1. Clonamos el repositorio**

```bash
git clone https://github.com/Ochoa-Stack/SkillStat.git
cd SkillStat
```

**2. Entramos a la carpeta del backend y creamos el entorno virtual**

El entorno virtual aísla las dependencias del proyecto para que no interfieran con otros proyectos en la misma maquina.

```bash
cd backend
# En Mac y Linux
python3 -m venv .venv
# En Windows
python -m venv .venv
```

**3. Activamos el entorno virtual**

Esto lo hacemos cada vez que abrimos una nueva terminal para trabajar en el proyecto. Todos los comandos de `pip`, `flask` y `python` de esta guia asumen que el entorno virtual ya esta activo.

```bash
# En Mac y Linux
source .venv/bin/activate
# En Windows (PowerShell)
.venv\Scripts\Activate.ps1
# En Windows (CMD)
.venv\Scripts\activate.bat
```

Cuando el entorno esta activo vemos `(.venv)` al inicio de la linea en la terminal.

**4. Instalamos las dependencias**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**5. Creamos la base de datos local**

Con PostgreSQL ya instalado y corriendo, creamos una base de datos vacia donde va a vivir el esquema del proyecto. Podemos hacerlo desde `psql` o desde pgAdmin4 si lo tenemos instalado:

```sql
CREATE DATABASE skillstat_dev;
```

El nombre `skillstat_dev` es el que usa el proyecto por convencion; si le ponemos otro nombre, hay que recordar ajustarlo tambien en `DATABASE_URL` en el paso 6.

**6. Configuramos las variables de entorno**

Copiamos el archivo de ejemplo y lo llenamos con los valores reales:

```bash
# En Mac y Linux
cp .env.example .env
# En Windows
copy .env.example .env
```

Abrimos `.env` y completamos cada variable. Nunca subimos el archivo `.env` al repositorio; solo `.env.example` vive en Git, sin valores reales. Guia rapida de que es cada cosa:

| Variable                                    | Que es                                                                                                      | De donde sale                                                                                                                              |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `SECRET_KEY`                                | Clave interna de Flask para firmar sesiones                                                                 | La inventamos nosotros, cualquier cadena larga y aleatoria                                                                                 |
| `DATABASE_URL`                              | Cadena de conexion a PostgreSQL                                                                             | La armamos con el usuario/password que definimos al instalar PostgreSQL y el nombre de la base de datos del paso 5                         |
| `JWT_SECRET_KEY`                            | Clave para firmar los tokens de sesion de la API                                                            | La inventamos nosotros, distinta a `SECRET_KEY`                                                                                            |
| `JWT_ACCESS_TOKEN_EXPIRES`                  | Cuanto dura la sesion antes de expirar, en segundos                                                         | Ya viene con un valor razonable (7200 = 2 horas), no hace falta tocarlo                                                                    |
| `JWT_COOKIE_SECURE`                         | Si las cookies de sesion exigen HTTPS                                                                       | En local se deja en `false`; en produccion se pone en `true`                                                                               |
| `GOOGLE_CLIENT_ID`                          | Id de cliente para el boton "Iniciar sesion con Google"                                                     | Ya viene precargado en `.env.example`, es compartido por el equipo, no hace falta generarlo de nuevo                                       |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`          | Credenciales de la API de empleos que alimenta el proyecto                                                  | Se piden en https://developer.adzuna.com/, pedirlas al equipo si ya existen unas compartidas                                               |
| `RESEND_API_KEY`                            | Credencial del servicio que envia los correos (verificacion de cuenta, recuperacion de contraseña, alertas) | Se genera en https://resend.com/, pedirla al equipo si ya existe una compartida                                                            |
| `BACKUP_STORAGE_URL` / `BACKUP_STORAGE_KEY` | Reservadas para almacenamiento externo de respaldos                                                         | Todavia no estan conectadas a ningun proveedor; se puede dejar el valor de ejemplo tal cual por ahora, no bloquea el arranque del proyecto |
| `SCHEDULER_ENABLED`                         | Si el pipeline diario de ingesta y calculo de tendencias corre automaticamente                              | Se deja en `false` en desarrollo para no gastar la cuota de la API de Adzuna mientras programamos                                          |
| `CORS_ORIGINS` / `FRONTEND_BASE_URL`        | De donde puede llamar el frontend a la API, y donde vive el frontend                                        | Ya vienen con los valores correctos para Live Server en local, no hace falta tocarlos salvo que sirvamos el frontend desde otro puerto     |

**7. Aplicamos las migraciones de base de datos**

Este paso crea todas las tablas dentro de `skillstat_dev`. Sin esto, el servidor arranca pero cualquier peticion que toque la base de datos va a fallar.

```bash
flask db upgrade
```

Si en algun punto el comando se queja de no encontrar la aplicacion, confirmamos que estamos parados en la carpeta `backend/` y que el entorno virtual esta activo.

**8. Corremos el servidor de desarrollo**

```bash
python run.py
```

Si todo esta bien veremos un mensaje indicando que Flask esta corriendo, generalmente en http://localhost:5000

**9. Servimos el frontend**

El frontend es HTML/CSS/JS plano, no necesita build. Lo mas simple es usar la extension Live Server de VS Code sobre la carpeta `frontend/`, apuntando al puerto 5500 (que ya es el que espera `CORS_ORIGINS` y `FRONTEND_BASE_URL` en el `.env` de ejemplo).

## Cuando algo no funciona

- Si `python` no se reconoce como comando, probamos con `python3`.
- Si el entorno virtual no se activa en Windows, es posible que
  necesitemos ejecutar primero:
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Si hay errores al instalar dependencias, verificamos que el entorno virtual este activado antes de correr `pip install`.
- Si `flask db upgrade` falla con un error de conexion, revisamos que PostgreSQL este corriendo y que `DATABASE_URL` tenga el usuario, contraseña, puerto y nombre de base de datos correctos.
- Si `pg_dump` o `pg_restore` no se reconocen como comando (solo necesario para trabajar con respaldos desde el panel de Admin), hay que agregar la carpeta `bin` de la instalacion de PostgreSQL al PATH del sistema.
- Para cualquier otro problema lo comentamos en el canal del equipo antes de intentar soluciones por cuenta propia.

## Comandos operativos de referencia

Esta seccion no es parte del levantamiento inicial del proyecto; es una referencia rapida para tareas que se hacen ya con el entorno funcionando.

**Generar un respaldo manual de la base de datos**

Se puede hacer desde el panel de Admin en el navegador (`/admin/respaldos.html`, requiere una cuenta con rol ADMIN), o directamente contra la API:

```bash
curl -X POST http://localhost:5000/api/admin/backup -H "Authorization: Bearer TU_TOKEN"
```

**Restaurar un respaldo**

Solo desde el panel de Admin, nunca directamente por API sin el flujo de confirmacion, la restauracion reemplaza todos los datos actuales de la base de datos. El panel exige escribir el nombre exacto del archivo antes de permitir confirmar, y genera automaticamente un respaldo de seguridad justo antes de ejecutar la restauracion.

**Poblar datos de ejemplo para desarrollo**

Después de aplicar las migraciones, si se quiere trabajar con algunos skills de ejemplo sin depender de la ingesta real de Adzuna (que consume cuota de API):

```bash
python scripts/seed_db.py
```

Esto es opcional dado que las categorías base ya se insertan automáticamente con `flask db upgrade`, este script solo agrega algunos skills de ejemplo para tener datos con los que probar el frontend sin ingesta real.

**Correr la ingesta de vacantes manualmente**

Con `SCHEDULER_ENABLED=false` (el valor por defecto en desarrollo), la ingesta no corre sola. Para dispararla manualmente y probar el pipeline:

```bash
curl -X POST http://localhost:5000/api/admin/ingest -H "Authorization: Bearer TU_TOKEN" -H "Content-Type: application/json" -d '{"pages": 1}'
```

Ojo con esto: cada llamada consume cuota real de la API de Adzuna, no se recomienda correrlo repetidamente sin necesidad.

**Activar el scheduler automatico**

Si se necesita que el pipeline diario (ingesta + calculo de tendencias + evaluacion de alertas) corra solo, se cambia `SCHEDULER_ENABLED=true` en `.env` y se reinicia el servidor. En desarrollo normal se deja en `false`.
