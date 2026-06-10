import os
import re

KEEP_PHRASES = [
    "Habilitamos nulos para",
    "Establecemos México como default",
    "Permitimos nulos en city_id",
    "Guardamos el hash de la",
    "Utilizamos llave primaria compuesta",
    "Relacionamos bidireccionalmente",
    "Forzamos unicidad combinada",
    "Restringimos los roles permitidos",
    "Protegemos la transacción con un",
    "Construimos la aplicación usando el patrón application factory",
    "crear instancias independientes según el",
    "Cargamos las variables de entorno antes de",
    "Hacemos esta validación aquí y no en la clase",
    "Importamos los modelos para que SQLAlchemy",
    "noqa",
]

def should_keep(line):
    for phrase in KEEP_PHRASES:
        if phrase in line:
            return True
    return False

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    modified = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#'):
            if not should_keep(line):
                modified = True
                continue
        new_lines.append(line)

    new_content = '\n'.join(new_lines)
    
    # Also clean up known unwanted docstrings
    unwanted_docstrings = [
        '    \"\"\"Configuración base compartida por todos los entornos\"\"\"\n',
        '    \"\"\"Configuración para el entorno de desarrollo local\"\"\"\n',
        '    \"\"\"Configuración para el entorno de producción\"\"\"\n',
        '    \"\"\"Configuración para el entorno de pruebas automatizadas\"\"\"\n',
        '    \"\"\"Crea y configura una instancia de la aplicación Flask\"\"\"\n',
        '    \"\"\"Conecta las extensiones con la instancia de la aplicación\"\"\"\n',
        '    \"\"\"Registra el endpoint de salud para verificar que el servicio está activo\"\"\"\n'
    ]
    for ud in unwanted_docstrings:
        if ud in new_content:
            new_content = new_content.replace(ud, "")
            modified = True

    # Remove consecutive blank lines
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

app_dir = os.path.join(os.getcwd(), 'app')
modified_files = []

for root, _, files in os.walk(app_dir):
    for file in files:
        if file.endswith('.py'):
            if clean_file(os.path.join(root, file)):
                modified_files.append(os.path.relpath(os.path.join(root, file), os.getcwd()))

for f in modified_files:
    print(f)
