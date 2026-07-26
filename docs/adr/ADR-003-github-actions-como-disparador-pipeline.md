# ADR-003: GitHub Actions como disparador externo del pipeline diario

## Estado
Aceptado

## Contexto
El pipeline diario de generación de datos (ingesta de vacantes, cálculo de tendencias, evaluación de alertas) corría originalmente mediante APScheduler dentro del mismo proceso Flask, disparado por un cron interno a medianoche.

Al desplegar en el tier gratuito de Render (ver [ADR-002](./ADR-002-servicios-separados-backend-frontend.md)), el Web Service se duerme tras 15 minutos de inactividad. Si el proceso está dormido a la hora programada, el job simplemente no se dispara, sin ningún error visible que lo señale; el pipeline deja de correr de forma silenciosa.

## Decisión
Usamos un workflow de GitHub Actions (`schedule: cron` diario, con `workflow_dispatch` disponible para disparo manual) que hace una petición HTTP real hacia un endpoint dedicado del backend, en vez de depender de un proceso interno que puede estar dormido.

## Alternativas consideradas
**Render Cron Jobs.** Descartado por no ser gratuito: se confirmó mediante búsqueda directa un costo mínimo de 1 USD al mes, aun para la configuración más económica disponible. GitHub Actions cumple el mismo propósito sin costo alguno para un repositorio del tamaño y volumen de ejecución de este proyecto.

**Disparo manual.** Descartado porque rompe la propuesta de valor central del proyecto: los datos deben actualizarse automáticamente cada día sin intervención humana. Un pipeline que depende de que alguien recuerde ejecutarlo manualmente no cumple esa promesa.

**Mantener el scheduler interno (APScheduler).** Descartado por incompatibilidad directa con el ciclo de sleep del tier gratuito de Render, que es la causa raíz del problema que esta decisión resuelve. Mantenerlo habría dejado el pipeline fallando de forma intermitente e indetectable.

## Consecuencias
El disparo del pipeline ya no depende del estado de actividad del Web Service, se ejecuta desde la infraestructura de GitHub, independiente de si el backend está dormido o despierto en ese momento (el propio request HTTP del workflow despierta al servicio si estaba dormido).

Se introduce una dependencia nueva sobre la disponibilidad de GitHub Actions como plataforma. El endpoint que recibe el disparo requiere su propio mecanismo de autenticación, independiente del sistema de usuarios existente (ver [ADR-004](./ADR-004-api-key-dedicada-para-pipeline.md)).

El workflow solo se indexa y ejecuta automáticamente desde la rama por defecto del repositorio. Mientras `main` no se actualice con este cambio, el disparo automático no ocurre todavía de forma real, solo verificable manualmente vía `curl` contra el endpoint.
