# Diagrama de Despliegue

Este diagrama representa la infraestructura real de producción de SkillStat, derivada directamente de las decisiones documentadas en [ADR-001](../adr/ADR-001-neon-como-proveedor-postgresql.md), [ADR-002](../adr/ADR-002-servicios-separados-backend-frontend.md) y [ADR-003](../adr/ADR-003-github-actions-como-disparador-pipeline.md).

```mermaid
%%{init: {"flowchart": {"curve": "stepBefore"}}}%%
flowchart LR
    %% 1. ORÍGENES (Columna Izquierda)
    subgraph Cliente["Navegador del usuario"]
        Browser["Cliente web"]
    end

    subgraph GitHub["GitHub"]
        Repo["Repositorio SkillStat"]
        Actions["GitHub Actions\ncron diario + workflow_dispatch"]
    end

    %% 2. CÓMPUTO (Columna Central)
    subgraph RenderInfra["Render (nodo de despliegue)"]
        StaticSite["Static Site\nskillstat-ss.onrender.com\nnunca duerme"]
        WebService["Web Service\nskillstat.onrender.com\ngunicorn run:app\nduerme tras 15 min de inactividad"]
    end

    %% 3. ALMACENAMIENTO (Columna Derecha)
    subgraph NeonInfra["Neon (nodo de datos)"]
        Postgres[("PostgreSQL\ntier gratuito permanente")]
    end

    subgraph R2Infra["Cloudflare R2 (nodo de respaldo)"]
        Bucket[("Bucket de respaldos\nvía boto3, egress cero")]
    end

    %% Relaciones de red y CI/CD
    Browser -->|HTTPS| StaticSite
    Browser -->|HTTPS, fetch API| WebService
    
    %% Retorno estático (El motor lo ruteará por el borde gracias a stepBefore)
    StaticSite -.->|sirve archivos estáticos| Browser

    Repo -->|deploy automático en push| StaticSite
    Repo -->|deploy automático en push| WebService
    Actions -->|POST /api/admin/trigger-pipeline\nX-Pipeline-Trigger-Key| WebService

    %% Relaciones de persistencia
    WebService -->|SQLAlchemy / Alembic| Postgres
    WebService -->|boto3, S3-compatible| Bucket

    %% Estilos minimalistas
    classDef neutral fill:#ffffff,stroke:#6b7280,stroke-width:1px,color:#000

    class Browser,StaticSite,WebService,Postgres,Bucket,Repo,Actions neutral
    
    style Cliente fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
    style GitHub fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
    style RenderInfra fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
    style NeonInfra fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
    style R2Infra fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
```

## Notas de infraestructura

El Web Service experimenta cold start de 30 a 60 segundos tras 15 minutos de inactividad, consecuencia aceptada de la decisión documentada en ADR-002. El Static Site nunca duerme bajo el mismo tier, por lo que la carga inicial de la interfaz no sufre ese retraso, solo las llamadas subsecuentes a la API.

El disparo del pipeline diario ocurre exclusivamente vía GitHub Actions hacia el endpoint dedicado, autenticado con una API key de un solo propósito (ver [ADR-004](../adr/ADR-004-api-key-dedicada-para-pipeline.md)), completamente al margen del sistema de autenticación de usuarios.
