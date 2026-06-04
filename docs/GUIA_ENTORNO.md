# Configuracion del entorno local

Esta guia explica como preparar la maquina para trabajar en SkillStat
desde cero. La seguimos la primera vez que clonamos el repositorio y
cada vez que alguien nuevo se integra al equipo.

## Lo que necesitamos tener instalado

- **Python 3.13.x** - lo descargamos desde https://www.python.org/downloads/
  Verificamos la instalacion con: `python --version`
- **Git** - lo descargamos desde https://git-scm.com/
  Verificamos con: `git --version`
- Un editor de codigo. Recomendamos Visual Studio Code.

## Pasos para configurar el proyecto

**1. Clonamos el repositorio**

```bash
git clone https://github.com/Ochoa-Stack/SkillStat.git
cd SkillStat
```

**2. Entramos a la carpeta del backend y creamos el entorno virtual**

El entorno virtual aísla las dependencias del proyecto para que no
interfieran con otros proyectos en la misma maquina.

```bash
cd backend

# En Mac y Linux
python3 -m venv .venv

# En Windows
python -m venv .venv
```

**3. Activamos el entorno virtual**

Esto lo hacemos cada vez que abrimos una nueva terminal para trabajar.

```bash
# En Mac y Linux
source .venv/bin/activate

# En Windows (PowerShell)
.venv\Scripts\Activate.ps1

# En Windows (CMD)
.venv\Scripts\activate.bat
```

Cuando el entorno esta activo vemos `(.venv)` al inicio de la linea
en la terminal.

**4. Instalamos las dependencias**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

> El archivo requirements.txt se completara en los proximos pasos del
> desarrollo. Si aun esta vacio este paso se puede omitir por ahora.

**5. Configuramos las variables de entorno**

Copiamos el archivo de ejemplo y lo llenamos con los valores reales:

```bash
# En Mac y Linux
cp .env.example .env

# En Windows
copy .env.example .env
```

Abrimos `.env` y completamos cada variable con los valores que se
nos proporcionen. Nunca subimos el archivo `.env` al repositorio.

**6. Corremos el servidor de desarrollo**

```bash
python run.py
```

Si todo esta bien veremos un mensaje indicando que Flask esta corriendo,
generalmente en http://localhost:5000

## Cuando algo no funciona

- Si `python` no se reconoce como comando, probamos con `python3`.
- Si el entorno virtual no se activa en Windows, es posible que
  necesitemos ejecutar primero:
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Si hay errores al instalar dependencias, verificamos que el entorno
  virtual este activado antes de correr `pip install`.
- Para cualquier otro problema lo comentamos en el canal del equipo
  antes de intentar soluciones por cuenta propia.
