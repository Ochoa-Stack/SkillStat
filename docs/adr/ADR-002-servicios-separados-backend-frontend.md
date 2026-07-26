# ADR-002: Servicios separados para backend y frontend en Render

## Estado
Aceptado

## Contexto
Al preparar el primer despliegue en producción, existía la opción de fusionar backend y frontend en un único Web Service de Render, sirviendo el frontend como archivos estáticos desde el mismo proceso Flask, o mantenerlos como dos servicios independientes: un Web Service para el backend y un Static Site para el frontend.

El backend ya estaba construido como una API JSON pura, sin ningún uso de `render_template` ni de `static_folder` de Flask en ningún punto del código existente. Esto significaba que fusionar ambos no era una continuación natural de la arquitectura ya construida, sino una modificación activa para acomodar una sola instancia de despliegue.

El tier gratuito de Render duerme los Web Services tras 15 minutos de inactividad, con un cold start de 30 a 60 segundos en el primer request posterior. Un Static Site en Render, en cambio, nunca duerme bajo ese mismo tier.

## Decisión
Usamos dos servicios independientes en Render: un Web Service para el backend Flask (`https://skillstat.onrender.com`) y un Static Site para el frontend (`https://skillstat-ss.onrender.com`), reflejando la separación de capas ya existente en el código (arquitectura orientada a servicios, con el backend como API pura).

## Alternativas consideradas
**Servicio único fusionado.** Evaluado explícitamente contra la separación. Habría requerido introducir `render_template` y `static_folder` en un backend que hasta ese momento no los usaba en ningún endpoint, es decir, una modificación de arquitectura motivada únicamente por conveniencia de despliegue, no por una necesidad real del sistema. Adicionalmente, fusionar ambos habría hecho que el frontend se durmiera junto con el backend en el ciclo de sleep del free tier, perdiendo la ventaja real de que un Static Site nunca duerme. Se descartó porque no resolvía ningún problema que la separación no resolviera ya, y sí introducía una regresión de disponibilidad para el frontend.

## Consecuencias
El proyecto opera con dos dominios `.onrender.com` distintos en vez de uno solo, lo que introdujo directamente el problema de cookies cross-site documentado en un ADR separado (ver ADR de SameSite). Esta es una consecuencia conocida y aceptada de la decisión, no un efecto secundario no previsto.

El frontend permanece siempre disponible sin cold start, mientras que el backend sí experimenta cold start tras inactividad, una asimetría consciente y aceptada: el costo de espera recae únicamente en las llamadas a la API, no en la carga inicial de la interfaz.

Si el proyecto migra en el futuro a un dominio propio con subdominios reales (`app.` y `api.`), esta separación en dos servicios se mantiene sin cambios estructurales; solo cambiaría el dominio detrás de cada uno.
