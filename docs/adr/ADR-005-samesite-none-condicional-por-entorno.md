# ADR-005: SameSite=None condicional por entorno para cookies JWT

## Estado
Aceptado

## Contexto
La separación de backend y frontend en dos servicios distintos de Render (ver [ADR-002](./ADR-002-servicios-separados-backend-frontend.md)) significa que ambos dominios `.onrender.com` son técnicamente cross-site entre sí, aunque compartan el mismo dominio raíz superficialmente.

Se confirmó con evidencia directa en el navegador (pestaña Application → Cookies) que ninguna cookie del backend llegaba a guardarse cuando el login se hacía desde el frontend: el valor original `JWT_COOKIE_SAMESITE="Lax"` hace que el navegador descarte la cookie en un escenario cross-site. Se confirmó también que `csrf_access_token` sufría exactamente el mismo rechazo, por compartir el mismo parámetro `samesite` dentro de Flask-JWT-Extended.

## Decisión
Usamos `JWT_COOKIE_SAMESITE` condicional según el entorno de ejecución: `"None"` en producción (que ya cuenta y requiere `Secure=True`), y `"Lax"` sin cambios en desarrollo y en testing, donde ambos servicios corren sobre el mismo origen (`localhost`) y no aplica el problema cross-site.

## Alternativas consideradas
No se evaluaron alternativas de arquitectura distintas a la ya decidida en ADR-002 (mantener servicios separados). El único camino alternativo real habría sido revertir esa decisión y fusionar ambos servicios bajo un mismo dominio, lo que ya fue descartado con su propia justificación independiente en ese documento.

## Consecuencias
La protección CSRF no se debilita con este cambio: el patrón Double Submit Cookie (`JWT_COOKIE_CSRF_PROTECT=True`) ya existente en el proyecto sigue operando de forma idéntica, independientemente del valor de `SameSite`.

Este es un fix correcto para la arquitectura actual de dos dominios `.onrender.com` distintos, pero no es la solución definitiva de largo plazo. Si el proyecto migra en el futuro a un dominio propio con `app.` y `api.` como subdominios reales del mismo dominio raíz, la solución definitiva sería volver a `SameSite=Lax`, aprovechando que subdominios de un mismo dominio raíz cuentan como same-site para el navegador.
