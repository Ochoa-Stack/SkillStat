# Arquitectura de SkillStat

SkillStat es una plataforma de inteligencia de mercado laboral que
recopila vacantes tecnologicas, extrae habilidades con procesamiento
de lenguaje natural y presenta los resultados en un dashboard analitico
llamado Panorama.

## Como esta organizado el repositorio

```
SkillStat/
├── frontend/     # Interfaz web: vistas, estilos y logica del cliente
├── backend/      # API REST, servicios, modelos y acceso a datos
├── data/         # Activos de datos para el procesamiento NLP
├── scripts/      # Herramientas de uso manual para el equipo
└── docs/         # Documentacion interna del proyecto
```

## Las capas del backend

El backend sigue una arquitectura en capas donde cada capa tiene una
responsabilidad clara y no invade la del resto:

| Capa | Donde vive | Que hace |
|------|-----------|----------|
| Controladores | `backend/app/controllers/` | Recibe peticiones HTTP y devuelve respuestas |
| Servicios | `backend/app/services/` | Contiene la logica de negocio del sistema |
| Repositorios | `backend/app/repositories/` | Habla con la base de datos |
| Modelos | `backend/app/models/` | Define la estructura de los datos |
| Clientes | `backend/clients/` | Se comunica con APIs externas |

Los controladores llaman a los servicios. Los servicios llaman a los
repositorios. Los repositorios hablan con la base de datos. Los clientes
son usados por los servicios para comunicarse con el exterior.

## Donde encontrar cada cosa

- Las rutas de la API viven en `backend/app/controllers/`
- La logica que procesa vacantes y extrae habilidades vive en `backend/app/services/`
- Las tablas de la base de datos estan definidas en `backend/app/models/`
- Las consultas a la base de datos viven en `backend/app/repositories/`
- Las conexiones con Adzuna, Nominatim y SendGrid viven en `backend/clients/`
- Las vistas HTML del Panorama y el resto de pantallas viven en `frontend/views/`
- Los archivos de estilos estan en `frontend/assets/css/`
- La logica del cliente esta en `frontend/assets/js/`
- El diccionario de habilidades tecnologicas vive en `data/dictionaries/`
