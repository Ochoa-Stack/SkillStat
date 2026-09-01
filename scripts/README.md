# scripts/

Aqui viven herramientas de uso manual para tareas de mantenimiento
y configuracion del proyecto. Estos scripts no forman parte de la
aplicacion y no se ejecutan automaticamente.

## Los scripts disponibles

**`seed_db.py`** - Carga los datos iniciales en la base de datos:
categorias de habilidades, ciudades base y el catalogo de habilidades
del diccionario ESCO. Se corre una sola vez al configurar un ambiente
nuevo.

**`build_dictionary.py`** - Descarga y procesa la taxonomia ESCO para
generar el archivo `data/dictionaries/skills_esco.jsonl`. Se corre
cuando actualizamos la version del diccionario.

**`backup_manual.py`** - Genera un respaldo de la base de datos de
forma manual sin pasar por la interfaz de administracion. Util para
respaldos puntuales antes de cambios importantes.

## Como correr un script

```bash
# Nos aseguramos de estar en la carpeta backend con el entorno activo
cd backend
source .venv/bin/activate   # Mac / Linux
.venv\Scripts\activate      # Windows

# Corremos el script desde la raiz del repositorio
python scripts/nombre_del_script.py
```
