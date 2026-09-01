# services/

Aqui vive la logica de negocio del sistema. Los servicios son el
corazon de SkillStat: procesan datos, toman decisiones y coordinan
el trabajo entre los distintos componentes.

## Lo que va aqui

- La logica que extrae habilidades de descripciones de vacantes
- La logica que calcula tendencias y metricas del mercado
- La logica que evalua alertas y decide cuando notificar
- La coordinacion entre repositorios y clientes externos

## Lo que no va aqui

Los servicios no conocen Flask. No manejan peticiones HTTP ni
construyen respuestas JSON. Tampoco acceden directamente a la base
de datos: para eso usan los repositorios.

## Los servicios del proyecto

| Archivo | Que hace |
|---------|----------|
| `ingestion_service.py` | Recopila vacantes desde la API de Adzuna |
| `skills_extraction_service.py` | Extrae habilidades tecnicas de descripciones |
| `market_trends_service.py` | Calcula metricas de demanda y tendencias |
| `alerts_service.py` | Evalua alertas y coordina las notificaciones |
| `backup_service.py` | Genera y restaura respaldos de la base de datos |
