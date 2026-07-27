# Diagrama de Casos de Uso - Vista de Alto Nivel

Este diagrama agrupa los treinta y tres casos de uso técnicos reales (ver [diagrama-casos-de-uso-completo.md](./diagrama-casos-de-uso-completo.md)) en capacidades funcionales de negocio, pensado para presentación y para lectura rápida del alcance del sistema, alineado con lo que evalúa el Requisito 7 (CRUD, autenticación y validaciones) de la materia.

```mermaid
%%{init: {"flowchart": {"curve": "stepBefore"}}}%%
flowchart LR
    %% Actores
    Visitante(["Visitante"])
    Registrado(["Usuario Registrado"])
    Admin(["Administrador"])

    %% Herencia de actores
    Registrado -.->|extiende| Visitante
    Admin -.->|extiende| Registrado

    %% Límite del Sistema
    subgraph Sistema["SkillStat"]
        %% Casos de uso de Visitante
        A(("Autenticarse y gestionar cuenta"))
        D(("Consultar Panorama del mercado laboral"))
        
        %% Casos de uso de Registrado
        B(("Gestionar perfil y habilidades"))
        C(("Configurar alertas de mercado"))
        
        %% Casos de uso de Admin
        E(("Administrar usuarios"))
        F(("Administrar respaldos"))
        G(("Administrar ingesta de datos"))
    end

    %% Relaciones
    Visitante --> A
    Visitante --> D

    Registrado --> B
    Registrado --> C

    Admin --> E
    Admin --> F
    Admin --> G

    %% Estilos UML (Neutros)
    classDef actor fill:#f3f4f6,stroke:#374151,stroke-width:2px,color:#000
    classDef uc fill:#ffffff,stroke:#6b7280,stroke-width:1px,color:#000
    
    class Visitante,Registrado,Admin actor
    class A,B,C,D,E,F,G uc
    style Sistema fill:transparent,stroke:#94a3b8,stroke-width:2px,stroke-dasharray: 5 5
```

## Correspondencia con el diagrama completo

| Capacidad | Casos de uso técnicos agrupados |
|---|---|
| Autenticarse y gestionar cuenta | Registro, login (password y Google), logout, verificación de correo, recuperación de contraseña |
| Gestionar perfil y habilidades | Ver/actualizar perfil, cambiar contraseña, brecha de habilidades, agregar/eliminar habilidad |
| Configurar alertas de mercado | Crear, listar, eliminar, activar/desactivar alerta |
| Consultar Panorama del mercado laboral | Catálogos, resumen, ranking, tendencias, distribución geográfica, salarios, comparación |
| Administrar usuarios | Listar usuarios, cambiar rol, cambiar estado |
| Administrar respaldos | Ejecutar, listar, restaurar respaldo |
| Administrar ingesta de datos | Disparar ingesta de vacantes |
