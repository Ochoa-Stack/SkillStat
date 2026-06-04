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
