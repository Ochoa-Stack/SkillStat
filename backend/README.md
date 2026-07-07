# backend/

Aqui vive la API REST, los servicios de negocio, los modelos de datos,
los repositorios y los clientes de APIs externas.

## Estructura principal

```
backend/
├── app/           # El nucleo de la aplicacion Flask
├── clients/       # Clientes para APIs externas
├── scheduler/     # Procesos automatizados periodicos
├── migrations/    # Migraciones de base de datos
├── tests/         # Pruebas unitarias e integracion
└── run.py         # Punto de entrada del servidor
```

## Como arranca la aplicacion

El archivo `run.py` inicia el servidor. La aplicacion se construye
en `app/__init__.py` usando el patron application factory, que permite
crear instancias independientes para desarrollo, produccion y pruebas.

## Variables de entorno

Todas las configuraciones sensibles (claves de API, URL de base de datos,
secreto JWT) viven en el archivo `.env`. Nunca se sube al repositorio.
El archivo `.env.example` muestra que variables se necesitan sin revelar
sus valores reales.

## Flujo de Ingesta y Snapshots

Para que los datos analíticos del sistema se mantengan actualizados, existe una secuencia obligatoria de dos comandos. **Siempre** se deben ejecutar en este orden antes de que los datos nuevos aparezcan en `/api/panorama/geo` o cualquier otra vista que consuma tendencias:

1. **Ingesta cruda:** `flask ingest-jobs --what "desarrollador" --pages 1`
   Extrae vacantes de Adzuna y las guarda en la base de datos (con su respectiva geolocalización a través de Nominatim). No clasifica habilidades ni calcula tendencias.

2. **Generación de Snapshots:** `flask generate-snapshots`
   Recalcula las métricas analíticas (TrendSnapshots) agrupando por habilidad, ciudad y estado usando los datos más recientes. Utiliza un upsert (ON CONFLICT DO UPDATE) por lo que es totalmente seguro y necesario ejecutarlo múltiples veces el mismo día sin perder la información ya existente.
