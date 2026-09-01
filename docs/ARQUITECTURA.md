# Arquitectura del Proyecto: SkillStat

Este documento define la estructura técnica oficial y las decisiones arquitectónicas de SkillStat. Cualquier desviación de este documento requiere un Architecture Decision Record (ADR) previo.

## 1. Visión General y Stack Tecnológico

SkillStat utiliza una arquitectura de Monorepo, aislando el frontend del backend.

- **Backend:** Python 3.13.x, Flask 3.x.
- **Base de Datos:** PostgreSQL 15.
- **ORM & Migraciones:** SQLAlchemy + Flask-Migrate (Alembic).
- **Frontend:** HTML, CSS, JavaScript Vanilla, Tailwind CSS.

## 2. Arquitectura Orientada a Servicios (SOA)

El backend está estrictamente separado en 4 capas para garantizar escalabilidad y evitar código espagueti:

1. **Capa de Presentación (Frontend):** Interfaces de usuario. Consume exclusivamente nuestra API REST.
2. **Capa de Procesos (Controladores):** Implementada mediante Flask Blueprints por dominio (`auth_bp`, `panorama_bp`, `alerts_bp`, `admin_bp`). Orquesta peticiones HTTP.
3. **Capa de Servicios (Lógica de Negocio):** Lógica pura. Contiene integraciones con APIs externas (Adzuna, Nominatim, SendGrid) y el procesamiento NLP. No sabe que Flask existe.
4. **Capa de Recursos (Repositorios y Datos):** Único punto de contacto con la base de datos. Implementa el patrón Repositorio (BaseRepository y repositorios específicos) aislando las consultas SQL.

## 3. Integridad de Datos (PostgreSQL)

El esquema relacional cuenta con 8 tablas base normalizadas estrictamente en la 3FN y BCNF. Toda operación de escritura en los repositorios está encapsulada en bloques `try/except` con `db.session.rollback()` para garantizar la integridad transaccional.
