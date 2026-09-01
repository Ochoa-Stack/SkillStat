# ADR-007: Savepoints para aislamiento de sesiones en la suite de pruebas

## Estado
Aceptado

## Contexto
La sesión con scope (`scoped_session`) que provee Flask-SQLAlchemy 3.x está diseñada para el ciclo de vida de una petición HTTP real, no para el ciclo de vida de una prueba individual dentro de una suite de pytest. Sin una estrategia explícita de aislamiento, cada prueba que hace `commit()` sobre la base de datos persiste esos cambios de forma real, contaminando el estado que verá la siguiente prueba y rompiendo la independencia que una suite de pruebas confiable requiere.

## Decisión
Usamos una sesión pura de SQLAlchemy configurada con `join_transaction_mode="create_savepoint"`, siguiendo la solución oficial documentada por SQLAlchemy 2.0 y Flask-SQLAlchemy 3.x para este problema específico.

Cada prueba corre dentro de una transacción global abierta al inicio. Todo `db.session.commit()` que el código de la aplicación ejecute durante la prueba no se escribe a disco: se consolida como un savepoint (transacción anidada) dentro de esa transacción global. Al finalizar la prueba, el teardown ejecuta un `rollback()` sobre la transacción global completa, descartando de golpe todos los savepoints acumulados y dejando la base de datos exactamente en el estado en que estaba antes de que la prueba comenzara.

## Alternativas consideradas
No se evaluaron alternativas de arquitectura propias frente a esta configuración: es la solución oficial y recomendada por la documentación de SQLAlchemy 2.0 y Flask-SQLAlchemy 3.x para el problema exacto de aislamiento de sesiones bajo pytest. La alternativa real frente a adoptarla no era un enfoque distinto igualmente válido, sino la ausencia de aislamiento automático confiable: dejar que cada prueba escribiera y persistiera cambios reales en la base de datos de test, con el riesgo de contaminación entre pruebas que eso implica.

## Consecuencias
La suite de pruebas queda verificada como confiablemente aislada tras tres corridas consecutivas limpias, sin contaminación de estado entre pruebas.

Esta estrategia asume que el código de la aplicación llama a `db.session.commit()` de forma normal, sin manejar transacciones anidadas propias que pudieran interferir con el savepoint que la suite ya está gestionando. Si en el futuro se introduce código que maneje sus propias transacciones anidadas explícitas, esa interacción debe revisarse contra este mecanismo antes de asumir que sigue funcionando sin cambios.
