# Cómo trabajamos en SkillStat

Este documento describe cómo organizamos el trabajo, cómo nos comunicamos
a través del historial de cambios y cómo escribimos código. Lo leemos todos
antes de tocar cualquier archivo del repositorio.

## Ramas del repositorio

Tenemos dos ramas permanentes que nunca se modifican directamente:

- `main` - contiene el código que está en producción. Solo recibe cambios
  desde `develop` a través de un Pull Request revisado y aprobado.
- `develop` - es la rama de trabajo activo del equipo. Aquí integramos
  todo antes de que llegue a producción.

Para cualquier tarea nueva creamos una rama temporal que nace desde
`develop` y muere cuando hacemos merge:

| Tipo | Cuándo usarla | Ejemplo |
|------|---------------|---------|
| `feature/` | Funcionalidad nueva | `feature/jwt-authentication` |
| `fix/` | Corrección de error en desarrollo | `fix/city-normalization` |
| `hotfix/` | Corrección urgente en producción | `hotfix/token-exposure` |
| `refactor/` | Reorganización sin cambiar comportamiento | `refactor/ingestion-cleanup` |
| `chore/` | Mantenimiento, dependencias, configuración | `chore/update-requirements` |
| `docs/` | Documentación únicamente | `docs/guia-entorno` |
| `test/` | Pruebas nuevas o actualizadas | `test/trends-service-unit` |
| `release/` | Preparación de versión para producción | `release/v1.0.0` |

Los nombres van en minúsculas, con guiones y sin acentos.

## Flujo de trabajo paso a paso

Cada vez que vamos a trabajar en algo seguimos estos pasos:

```bash
# Nos aseguramos de que develop esté al día antes de empezar
git checkout develop
git pull origin develop

# Creamos nuestra rama desde develop
git checkout -b feature/nombre-descriptivo

# Trabajamos y guardamos nuestros avances en commits
git add .
git commit -m "feat(scope): descripcion del cambio"

# Mantenemos nuestra rama sincronizada con develop mientras trabajamos
git fetch origin
git rebase origin/develop

# Subimos nuestra rama y abrimos el Pull Request hacia develop
git push origin feature/nombre-descriptivo
```

Nadie toca `main` ni `develop` directamente. Todo pasa por un Pull Request.
Nadie hace merge de su propio trabajo sin que alguien más lo haya revisado.
Después del merge borramos la rama.

## Formato de commits

Cada commit sigue esta estructura:

```
tipo(alcance): descripcion breve en imperativo
```

Los tipos disponibles:

| Tipo | Cuándo usarlo |
|------|---------------|
| `feat` | Funcionalidad nueva |
| `fix` | Corrección de error |
| `docs` | Cambio de documentación |
| `style` | Formato sin cambio de lógica |
| `refactor` | Reorganización sin cambio de comportamiento |
| `test` | Agregar o modificar pruebas |
| `chore` | Mantenimiento, dependencias, configuración |
| `perf` | Mejora de rendimiento |

Ejemplos reales del proyecto:

```
feat(auth): implement JWT login and token validation
fix(nlp): resolve phrase matcher failure on multi-word skills
chore(deps): add Flask-JWT-Extended and spaCy to requirements
docs(contributing): add commit format and branching guide
test(trends): add unit tests for weekly growth rate calculation
refactor(ingestion): isolate Adzuna client from ingestion logic
```

## Cómo escribimos comentarios en el código

Comentamos solo cuando el código por sí solo no deja clara la intención
detrás de lo que hace. Si el código se entiende solo, no ponemos comentario.

El comentario explica el por qué, no el qué. El qué ya lo dice el código.

Escribimos en primera persona del plural, en español, sin tecnicismos,
sin emojis y sin numerar los pasos. Aplica a todos los lenguajes del
proyecto: Python, JavaScript, CSS e HTML.

Así escribimos:

```python
# Descartamos las vacantes que ya procesamos para no duplicar los resultados.
pending = jobs.filter(processed=False)

# Guardamos el hash para detectar si la descripcion cambio en la fuente original.
job.description_hash = compute_hash(raw_description)

# Si el umbral ya se supero avisamos al usuario antes de continuar.
if demand_count >= alert.threshold:
    notify_user(alert)
```

```javascript
// Esperamos el token antes de hacer la peticion para no enviar una solicitud sin autenticar.
const token = await getAuthToken();

// Mostramos el mensaje directamente para que el usuario sepa que paso sin tener que buscar.
showErrorMessage(error.message);
```

Así no escribimos:

```python
# 1. Filtramos los jobs
# Funcion para filtrar vacantes usando ORM
# Filter unprocessed jobs from database
# 🔍 Buscamos vacantes sin procesar
```

## Reglas que no se negocian

- Nadie hace push directo a `main` ni a `develop`.
- Nadie hace merge de su propio Pull Request sin revision previa.
- Un commit representa un solo cambio logico. No mezclamos cosas distintas.
- No dejamos deuda tecnica sin documentar. Si algo quedo incompleto
  abrimos un issue o lo anotamos en el PR.
- Si una rama lleva mas de una semana sin actividad, revisamos si sigue
  siendo necesaria o la cerramos.