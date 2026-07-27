# ADR-006: Cloudflare R2 como backend de almacenamiento para respaldos remotos

## Estado
Aceptado

## Contexto
SkillStat requería un backend de almacenamiento remoto para sus respaldos de base de datos, con dos restricciones no negociables dado el carácter de portafolio del proyecto y la ausencia de presupuesto de infraestructura (ver sección de restricciones de la materia): costo cero de operación sostenida, y un tier gratuito que no expire con el tiempo ni con el uso normal esperado del proyecto.

El criterio decisivo no fue el costo de almacenamiento en sí, a esa escala de datos, la diferencia entre proveedores es de centavos sino el costo de egress: cuánto cobra cada proveedor por sacar datos hacia fuera de su plataforma, que es exactamente la operación que ocurre cada vez que se restaura un respaldo.

## Decisión
Usamos Cloudflare R2, integrado vía su API compatible con S3 mediante `boto3`, como backend de almacenamiento remoto para los respaldos de la base de datos.

## Alternativas consideradas
**Amazon S3.** Descartado por su estructura de egress: cobra 0.09 USD por GB de datos transferidos hacia fuera después de los primeros 100 GB gratuitos al mes. R2 no cobra nada por egress bajo ninguna circunstancia. Para un proceso de restauración de respaldo que es egress por definición, esto representa un costo recurrente que R2 elimina por completo, sin importar cuántas veces se necesite restaurar. El almacenamiento en sí también es más económico en R2 (0.015 USD por GB al mes frente a 0.023 USD por GB en S3), pero esa diferencia es secundaria frente al ahorro en egress.

**Google Cloud Storage.** Descartado sin llegar a una comparación de pricing detallada: introducir un tercer proveedor de nube distinto a los ya usados en el proyecto (Render, Neon) habría sumado una cuenta y un panel de administración adicionales sin ninguna ventaja concreta sobre R2 en cuanto al criterio decisivo (egress cero), que GCS no ofrece de forma nativa.

## Consecuencias
Los respaldos pueden restaurarse tantas veces como sea necesario sin que el costo de transferencia se convierta en una variable a monitorear, lo cual es particularmente relevante considerando que ya se documentó un incidente real de restauración de respaldo con desincronización de esquema (ver rama test/backup-restore-coverage `PR #54`), escenario que en un proveedor con egress de pago habría tenido, además del costo de ingeniería, un costo económico directo por cada intento de recuperación.

R2 implementa un subconjunto de la API de S3, no su totalidad, funciones avanzadas como S3 Object Lock o Intelligent-Tiering no tienen equivalente directo. Esto no representa una limitación real para el caso de uso actual del proyecto (subir y descargar archivos de respaldo), pero queda como restricción conocida si el uso del almacenamiento remoto se expandiera a necesidades más complejas en el futuro.
