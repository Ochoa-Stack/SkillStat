# Diagrama de Componentes

Este diagrama representa la arquitectura por capas real de SkillStat, derivada de los cinco controladores, los nueve servicios de `backend/app/services/`, y las integraciones externas confirmadas en el código. Los servicios nunca acceden a la base de datos directamente ni conocen Flask; median siempre a través de repositorios, según la regla explícita documentada en `backend/app/services/README.md`.

```mermaid
%%{init: {"flowchart": {"curve": "stepBefore"}}}%%
flowchart LR
    %% 1. PRESENTACIÓN
    subgraph Presentacion["Capa de Presentación (Controllers)"]
        AdminBP["admin_bp"]
        AlertsBP["alerts_bp"]
        AuthBP["auth_bp"]
        PanoramaBP["panorama_bp"]
        ProfileBP["profile_bp"]
    end

    %% 2. APLICACIÓN
    subgraph Aplicacion["Capa de Aplicación (Services)"]
        IngestionS["IngestionService"]
        SkillsExtractionS["SkillsExtractionService\n(motor spaCy + EntityRuler)"]
        MarketTrendsS["MarketTrendsService\n(pandas)"]
        AlertsS["AlertsService"]
        BackupS["BackupService\n(pg_dump / pg_restore)"]
        EmailS["EmailService"]
        ProfileS["ProfileService"]
        StorageS["RemoteStorageService\n(boto3)"]
    end

    %% 3. INFRAESTRUCTURA
    subgraph Infraestructura["Capa de Infraestructura (Repositories)"]
        Repos[("Repositorios\nuser, job, skill, job_skill,\nalert, trend_snapshot, backup, city")]
        DB[("PostgreSQL")]
    end

    %% 4. SERVICIOS EXTERNOS
    subgraph Externos["Servicios Externos"]
        Adzuna[["Adzuna API"]]
        Nominatim[["Nominatim\nOpenStreetMap"]]
        Resend[["Resend API"]]
        R2[["Cloudflare R2"]]
    end

    %% Relaciones Presentación -> Aplicación
    AdminBP --> IngestionS
    AdminBP --> BackupS
    ProfileBP --> ProfileS
    AuthBP --> EmailS

    %% Relaciones Presentación -> Infraestructura (Bypass arquitectónico)
    AlertsBP --> Repos
    AuthBP --> Repos
    PanoramaBP --> Repos

    %% Relaciones Aplicación -> Infraestructura / Externos / Internos
    IngestionS --> SkillsExtractionS
    IngestionS --> Repos
    IngestionS --> Adzuna
    
    MarketTrendsS --> Repos
    
    AlertsS --> Repos
    AlertsS --> EmailS
    
    BackupS --> StorageS
    BackupS --> DB
    
    ProfileS --> Repos
    ProfileS -.->|hash de contraseña| Repos
    
    EmailS --> Resend
    StorageS --> R2

    %% Relaciones Infraestructura -> Base de Datos / Externos
    Repos --> DB
    Repos -.->|geocodificación de ciudad| Nominatim

    %% Estilos minimalistas
    classDef neutral fill:#ffffff,stroke:#6b7280,stroke-width:1px,color:#000

    class AdminBP,AlertsBP,AuthBP,PanoramaBP,ProfileBP neutral
    class IngestionS,SkillsExtractionS,MarketTrendsS,AlertsS,BackupS,EmailS,ProfileS,StorageS neutral
    class Repos,DB neutral
    class Adzuna,Nominatim,Resend,R2 neutral
    
    style Presentacion fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
    style Aplicacion fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
    style Infraestructura fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
    style Externos fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
```

## Notas de fidelidad al código

`AdminBP` también invoca directamente a `MarketTrendsService` y `AlertsService` a través del endpoint `/trigger-pipeline`, ya representado en el [diagrama de secuencia de alertas](./diagrama-secuencia-alertas.md); se omite esa flecha aquí para no duplicar la misma relación en dos diagramas con propósitos distintos.

`BackupService` no delega en un repositorio para la ejecución física del respaldo, invoca `pg_dump`/`pg_restore` directamente vía `subprocess`, razón por la cual se conecta a `PostgreSQL` de forma directa en este diagrama, a diferencia del resto de los servicios que median siempre por `Repositorios`. Esta es una excepción real y documentada en el propio código (comentarios de `backup_service.py` explican la necesidad de cerrar la sesión de SQLAlchemy antes de invocar `pg_restore` para evitar deadlocks), no una inconsistencia del diagrama.

`RemoteStorageService` (Cloudflare R2) actúa como capa de resiliencia adicional sobre el respaldo local ya existente, nunca como mecanismo único: si R2 no está configurado o falla, el respaldo local generado por `BackupService` sigue siendo válido, según lo documentado en [ADR-006](../adr/ADR-006-cloudflare-r2-para-respaldo-remoto.md).
