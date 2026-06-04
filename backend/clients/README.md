# clients/

Aqui viven los clientes que se comunican con APIs externas. Cada archivo
envuelve una sola API y expone metodos claros para que los servicios
puedan usarla sin conocer los detalles de la comunicacion HTTP.

## Lo que va aqui

- La logica de autenticacion con cada API externa
- El manejo de errores y reintentos de conexion
- La transformacion de la respuesta al formato que el sistema necesita

## Los clientes del proyecto

| Archivo | API que envuelve |
|---------|-----------------|
| `adzuna_client.py` | Adzuna Jobs API - fuente de vacantes |
| `nominatim_client.py` | Nominatim / OpenStreetMap - geocodificacion |
| `sendgrid_client.py` | SendGrid - envio de correos de alerta |
| `base_client.py` | Logica compartida: reintentos, timeouts, headers |

Los servicios nunca llaman directamente a `requests` o `httpx`.
Siempre usan estos clientes.
