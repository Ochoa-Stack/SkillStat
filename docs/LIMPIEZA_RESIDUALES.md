# Eliminación de archivos residuales de sesiones de debug [1]

## Contexto

Durante la auditoría técnica pre-Ronda 14 se detectaron cuatro archivos no planificados en backend/ que fueron generados durante sesiones de depuración manual y nunca formaron parte del scaffold del proyecto:

- backend/clean.py (80 líneas)
- backend/clean2.py (79 líneas)
- backend/clean3.py (78 líneas)
- backend/test_read.py (13 líneas)

Los archivos fueron eliminados del working tree de develop durante la sesión de diagnóstico. Esta rama los elimina formalmente del historial mediante este registro de decisión.

## Decisión

Se eliminan sin recuperación. No contenían lógica de aplicación, pruebas formales ni configuración. Eran scripts ad-hoc de depuración sin valor para el proyecto.

## Consecuencias

El directorio backend/ queda alineado con el scaffold original. Cualquier utilidad de depuración futura debe crearse en backend/tests/ o en scripts/ con nombre descriptivo y commitearse como parte del flujo normal de desarrollo.
