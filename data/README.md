# data/

Aqui viven los activos de datos que usa el modulo de procesamiento
de lenguaje natural. No es codigo de la aplicacion: son los archivos
que alimentan al extractor de habilidades.

## Lo que hay aqui

- `dictionaries/skills_esco.jsonl` - habilidades tecnicas de la
  taxonomia ESCO (base de datos oficial de la Union Europea). Se
  descarga y procesa con el script `scripts/build_dictionary.py`.
- `dictionaries/skills_custom.jsonl` - habilidades que el equipo
  agrega manualmente cuando la taxonomia base no las incluye.
- `dictionaries/skill_aliases.json` - mapeo de abreviaciones y
  variantes al nombre canonico. Por ejemplo: `"JS": "JavaScript"`.
- `samples/vacantes_sample.json` - vacantes de prueba para
  desarrollar y probar el extractor sin consumir la API real.

## Como agregar una habilidad nueva

Si encontramos una habilidad que el sistema no detecta, la agregamos
en `skills_custom.jsonl` siguiendo el mismo formato que el resto
del archivo. Si es una abreviacion, la agregamos en `skill_aliases.json`.
