# ADR-001: Neon como proveedor de PostgreSQL sobre Render Postgres

## Estado
Aceptado

## Contexto
SkillStat requería una base de datos PostgreSQL gestionada para su primer despliegue en producción. La evaluación se hizo contra el estado real del mercado free-tier en julio de 2026, no contra documentación heredada o supuestos de sesiones anteriores.

Render ofrece PostgreSQL gestionado como parte de su ecosistema, lo que en principio simplificaría la arquitectura al mantener base de datos y aplicación bajo el mismo proveedor. Sin embargo, se confirmó mediante búsqueda directa que las bases de datos gratuitas de Render expiran a los 30 días de creadas, con solo 14 días de gracia posteriores y sin mecanismo de respaldo nativo incluido en el tier gratuito. Esta condición contradecía documentación previa que el equipo tenía registrada, que indicaba incorrectamente una expiración a 90 días.

Railway se descartó de la evaluación sin llegar a comparación detallada: ya no ofrece un tier gratuito real y exige método de pago desde el trial.

## Decisión
Usamos Neon como proveedor de PostgreSQL para el entorno de producción.

Neon ofrece un tier gratuito permanente sin fecha de expiración, sin requerir tarjeta de crédito, con 0.5 GB de almacenamiento y 100 horas de cómputo mensuales. Es compatible al 100% con PostgreSQL estándar, sin ser un fork con comportamiento divergente, lo que no introduce riesgo de incompatibilidad con SQLAlchemy, Alembic, ni con ninguna sentencia SQL ya escrita para el proyecto.

## Alternativas consideradas
**Render Postgres.** Descartado por la expiración real de 30 días en el tier gratuito (confirmada contra el estado actual del servicio, no contra documentación desactualizada), los 14 días de gracia insuficientes para una migración de emergencia sin aviso previo, y la ausencia de respaldo nativo en ese mismo tier. Mantener aplicación y base de datos bajo el mismo proveedor no compensaba el riesgo de pérdida de datos por expiración silenciosa.

**Railway.** Descartado antes de una comparación técnica profunda: la ausencia de tier gratuito real sin método de pago lo sacaba de consideración para las restricciones del proyecto (sin presupuesto asignado para infraestructura).

## Consecuencias
La base de datos de producción vive en un proveedor distinto al de hosting de la aplicación (Render), lo que introduce una dependencia externa adicional a monitorear, pero elimina el riesgo de expiración que Render Postgres habría representado.

Queda como responsabilidad activa monitorear el consumo real contra los límites del tier gratuito de Neon (0.5 GB de almacenamiento, 100 horas de cómputo mensual), dado que superar esos límites sí tiene consecuencia directa sobre la disponibilidad del servicio, a diferencia de una simple expiración por tiempo.
