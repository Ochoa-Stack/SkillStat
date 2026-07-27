# Diagrama de Secuencia: Generación y Envío de Alertas

Este diagrama ilustra el flujo completo del pipeline diario de alertas, desde el disparo externo hasta la notificación al usuario. Es el flujo que representa el núcleo funcional de la propuesta de valor de SkillStat: la entrega proactiva de cambios relevantes en el mercado laboral, no solo su consulta pasiva.

Se eligió este flujo como el diagrama de secuencia ancla del proyecto por sobre el flujo de login, porque conecta directamente tres decisiones arquitectónicas ya documentadas ([ADR-003](../adr/ADR-003-github-actions-como-disparador-pipeline.md), [ADR-004](../adr/ADR-004-api-key-dedicada-para-pipeline.md)) con la lógica de negocio real del sistema.

```mermaid
sequenceDiagram
    autonumber

    box transparent "Desencadenador"
        participant GHA as GitHub Actions
    end

    box transparent "Presentación / API"
        participant EP as Endpoint /trigger-pipeline
    end

    box transparent "Capa de Aplicación (Core)"
        participant MTS as MarketTrendsService
        participant AS as AlertsService
    end

    box transparent "Infraestructura (Datos)"
        participant Repo as Repositorios\n(alert, skill, trend_snapshot, user)
        participant DB as PostgreSQL
    end

    box transparent "Infraestructura (Notificaciones)"
        participant ES as EmailService
        participant Resend as Resend API
    end

    GHA->>EP: POST /api/admin/trigger-pipeline\nheader X-Pipeline-Trigger-Key
    EP->>EP: hmac.compare_digest(key, PIPELINE_TRIGGER_SECRET)

    alt Key inválida
        EP-->>GHA: 401 Unauthorized
    else Key válida
        EP->>MTS: generate_snapshots()
        MTS->>Repo: consulta job_skills recientes
        Repo->>DB: SELECT
        DB-->>Repo: filas
        Repo-->>MTS: datos agregados
        
        MTS->>Repo: guarda trend_snapshots
        Repo->>DB: INSERT trend_snapshots
        DB-->>Repo: confirmación de guardado
        Repo-->>MTS: éxito
        
        MTS-->>EP: snapshots_generated

        EP->>AS: evaluate_and_notify()
        AS->>Repo: obtiene alertas activas (active = true)
        Repo->>DB: SELECT user_alerts
        DB-->>Repo: alertas activas
        Repo-->>AS: lista de alertas

        loop Por cada alerta activa
            AS->>Repo: obtiene snapshot más reciente de la skill
            Repo-->>AS: trend_snapshot
            AS->>AS: evalúa umbral\n(threshold_value o threshold_percentage\nsegún alert_type)

            alt Umbral cumplido
                AS->>ES: send_alert_email(user, skill, snapshot)
                ES->>Resend: POST /emails
                Resend-->>ES: 200 OK
            else Umbral no cumplido
                AS->>AS: descarta, continúa loop
            end
        end

        AS-->>EP: notifications_sent
        EP-->>GHA: 200 {snapshots_generated, notifications_sent}
    end
```

## Notas del flujo

La autenticación del endpoint ocurre antes de cualquier trabajo real, descartando peticiones no autorizadas sin tocar la base de datos, según lo decidido en ADR-004.

La evaluación de umbral distingue entre alertas de tipo `ABSOLUTE` (comparación directa contra `threshold_value`) y `TREND` (comparación contra `threshold_percentage`), restricción impuesta a nivel de base de datos mediante `CheckConstraint` en el modelo `Alert`, no solo a nivel de lógica de aplicación.

El envío real de correos depende de Resend, actualmente en modo sandbox, lo que significa que solo la cuenta propietaria de la API key recibe correos reales sin importar cuántas alertas se generen para otros usuarios. Esta limitación queda documentada como deuda activa fuera del alcance de este diagrama.
