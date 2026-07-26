# Modelo Entidad-Relación

Este diagrama representa la estructura relacional completa de la base de datos de SkillStat, derivada directamente de los trece modelos SQLAlchemy definidos en `backend/app/models/`. Las cardinalidades y nulabilidades reflejan exactamente las restricciones declaradas en el código, no una interpretación aproximada del dominio.

`JobSkill` y `UserSkill` se modelan como entidades propias, no como simples líneas de relación muchos-a-muchos, porque ambas llevan llave primaria compuesta y columnas adicionales (`confidence_score` en la primera, `created_at` en ambas), cumpliendo con el patrón de Association Object que exige la tercera forma normal.

## Notación

`||` indica exactamente uno. `|o` indica cero o uno. `o{` indica cero o muchos. `|{` indica uno o muchos. `PK` marca llave primaria, `FK` llave foránea, `UK` restricción de unicidad.

```mermaid
%%{init: { 'er': { 'layoutDirection': 'LR' } } }%%
erDiagram
    %% 1. NÚCLEO DE USUARIOS Y AUTENTICACIÓN
    USERS ||--o{ OAUTH_ACCOUNTS : "vincula"
    USERS ||--o{ PASSWORD_RESET_TOKENS : "solicita"
    USERS ||--o{ EMAIL_VERIFICATION_TOKENS : "solicita"
    USERS |o--o{ BACKUPS : "genera"

    %% 2. TABLAS PUENTE / INTERSECCIÓN (Centro geométrico)
    USERS ||--o{ USER_SKILLS : "declara"
    USERS ||--o{ ALERTS : "configura"
    SKILLS ||--o{ USER_SKILLS : "declarada por"
    SKILLS ||--o{ ALERTS : "monitoreada por"

    %% 3. NÚCLEO CORE: MERCADO Y HABILIDADES
    CATEGORIES ||--o{ SKILLS : "clasifica"
    JOBS ||--o{ JOB_SKILLS : "requiere"
    SKILLS ||--o{ JOB_SKILLS : "detectada en"

    %% 4. NÚCLEO GEOGRÁFICO Y ANALÍTICA
    CITIES |o--o{ JOBS : "ubica"
    CITIES |o--o{ TREND_SNAPSHOTS : "ubica"
    SKILLS ||--o{ TREND_SNAPSHOTS : "medida en"

    %% DEFINICIÓN DE ENTIDADES (El orden aquí no afecta el renderizado, solo las relaciones de arriba)

    CATEGORIES {
        int id PK
        string name UK
    }

    CITIES {
        int id PK
        string name UK
        string state
        string country
        decimal lat
        decimal lon
    }

    SKILLS {
        int id PK
        string name
        string canonical_name UK
        int category_id FK
    }

    JOBS {
        int id PK
        string source
        string title
        string company
        int city_id FK
        decimal salary_min
        decimal salary_max
        text raw_description
        string description_hash UK
        boolean processed
        datetime created_at
        datetime updated_at
    }

    JOB_SKILLS {
        int job_id PK, FK
        int skill_id PK, FK
        decimal confidence_score
        datetime created_at
    }

    USERS {
        int id PK
        string email UK
        string first_name
        string last_name
        string password_hash
        string role
        datetime created_at
        datetime password_changed_at
        string intent
        datetime email_verified_at
        boolean is_active
    }

    USER_SKILLS {
        int user_id PK, FK
        int skill_id PK, FK
        datetime created_at
    }

    OAUTH_ACCOUNTS {
        int id PK
        int user_id FK
        string provider
        string provider_user_id
        datetime created_at
    }

    PASSWORD_RESET_TOKENS {
        int id PK
        int user_id FK
        string token_hash UK
        datetime expires_at
        datetime used_at
        datetime created_at
    }

    EMAIL_VERIFICATION_TOKENS {
        int id PK
        int user_id FK
        string token_hash UK
        datetime expires_at
        datetime used_at
        datetime created_at
    }

    ALERTS {
        int id PK
        int user_id FK
        int skill_id FK
        string alert_type
        int threshold_value
        decimal threshold_percentage
        boolean active
        datetime created_at
    }

    TREND_SNAPSHOTS {
        int id PK
        int skill_id FK
        int city_id FK
        date date
        int demand_count
        decimal growth_rate
        decimal avg_salary
    }

    BACKUPS {
        int id PK
        int user_id FK
        string filename
        string storage_url
        datetime created_at
        string status
        bigint file_size_bytes
    }
```

## Notas estructurales

`PasswordResetToken` y `EmailVerificationToken` tienen su llave foránea configurada con `ondelete="CASCADE"`, así que al eliminar un usuario sus tokens pendientes se eliminan junto con él a nivel de base de datos, aunque el modelo `User` no declara `relationship()` explícita hacia ninguno de los dos, a diferencia del resto de sus relaciones. El acceso a esos tokens ocurre siempre a través de su repositorio correspondiente, no por
navegación directa desde el objeto usuario.

Las llaves foráneas nulables de este modelo son tres: `city_id` en `Job` y en `TrendSnapshot`, permitiendo vacantes o métricas sin geolocalización resuelta, y `user_id` en `Backup`, permitiendo respaldos automáticos ejecutados por el scheduler sin un usuario físico asociado.
