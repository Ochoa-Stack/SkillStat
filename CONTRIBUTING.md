# Normativa de Colaboración y Desarrollo

Este documento establece las reglas operativas inquebrantables para el equipo de SkillStat. No son sugerencias, son requisitos para la integración de código.

## 1. Flujo de Git y Ramas
* **Ramas Protegidas:** `main` y `develop` están protegidas. Nadie hace un push directo a estas ramas bajo ninguna circunstancia.
* **Nomenclatura de Ramas:** Toda rama nueva se crea a partir de `develop` utilizando el formato: `tipo/descripcion-en-kebab-case` (ej. `feature/sqlalchemy-models`).
* **Integración:** Todo código entra a `develop` exclusivamente mediante un Pull Request revisado. No se deja deuda técnica sin corregir.

## 2. Historial y Commits (Conventional Commits)
Cada sub-ronda o bloque de trabajo debe ser un commit atómico. El mensaje debe seguir el estándar:
`tipo(scope): descripción en imperativo`
Tipos permitidos: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`.

## 3. Convención Estricta de Comentarios en Código
Todo comentario debe explicar el **POR QUÉ**, nunca el **QUÉ**.
* **Regla:** Si el código no deja clara la intención por sí solo, refactoriza. Si la regla de negocio es compleja, se comenta el razonamiento.
* **Tono:** Primera persona del plural implícita en español. Sin tecnicismos innecesarios, sin emojis, sin numeración de pasos.
* **Correcto:** `Descartamos las vacantes ya procesadas para no duplicar los resultados.`
* **Incorrecto:** `Filtramos jobs / Función para filtrar`

## 4. Seguridad
* El archivo `.env` nunca se sube al repositorio.
* Las contraseñas se manejan siempre mediante hashes (bcrypt) y el acceso a rutas protegidas se valida estrictamente por roles mediante tokens JWT.