# ADR-004: API key dedicada para autenticar el endpoint de disparo del pipeline

## Estado
Aceptado

## Contexto
El endpoint `POST /api/admin/trigger-pipeline`, introducido junto con la decisión de usar GitHub Actions como disparador externo (ver [ADR-003](./ADR-003-github-actions-como-disparador-pipeline.md)), necesitaba un mecanismo de autenticación propio. El sistema de autenticación existente del proyecto está construido sobre JWT en cookies httpOnly, un esquema diseñado para sesiones de navegador con un usuario humano detrás.

GitHub Actions no tiene navegador ni maneja cookies, por lo que el esquema de autenticación ya existente no era utilizable directamente para este caso sin adaptaciones adicionales.

## Decisión
Usamos un header dedicado (`X-Pipeline-Trigger-Key`) validado con `hmac.compare_digest` contra un secreto almacenado en una variable de entorno de un solo propósito (`PIPELINE_TRIGGER_SECRET`), completamente separado del sistema de JWT y roles ya existente.

## Alternativas consideradas
**JWT de larga duración de un admin real.** Descartado porque mezclaría la identidad de una persona real con un proceso automatizado. Si ese admin cambia de contraseña, revoca sus tokens, o su cuenta se desactiva por cualquier razón administrativa, el pipeline automatizado se rompería como efecto colateral de una acción que no tiene relación alguna con él. Además, un JWT de larga duración es una superficie de ataque mayor que una API key de un solo propósito: si se filtra, otorga todos los permisos de ese usuario admin, no solo la capacidad de disparar el pipeline.

## Consecuencias
El endpoint de disparo del pipeline queda completamente desacoplado del sistema de usuarios: no pasa por `role_required`, no depende de ningún JWT, y no se ve afectado por cambios en las cuentas de administradores reales.

Se introduce una variable de entorno adicional (`PIPELINE_TRIGGER_SECRET`) que requiere el mismo tratamiento de secreto que cualquier otra credencial del proyecto: nunca se transcribe en documentación, nunca se comitea, y tiene guard incondicional de arranque equivalente al ya existente para otras claves de servicios externos.

La comparación se hace con `hmac.compare_digest` en vez de una comparación directa de strings, para evitar ataques de temporización (timing attacks) sobre la validación del secreto.
