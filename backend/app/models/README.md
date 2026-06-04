# models/

Aqui definimos la estructura de los datos del sistema usando SQLAlchemy.
Cada archivo representa una tabla de la base de datos.

## Lo que va aqui

- La definicion de columnas, tipos de dato y restricciones
- Las relaciones entre tablas (claves foraneas, backrefs)
- Las restricciones de integridad (UNIQUE, CHECK, NOT NULL)

## Lo que no va aqui

La logica de negocio no vive en los modelos. Los modelos describen
la forma de los datos, no lo que hacemos con ellos.

## Las entidades del proyecto

`category`, `city`, `skill`, `job`, `job_skill`, `user`, `alert`,
`trend_snapshot`, `backup`.

El diagrama entidad-relacion completo esta en `docs/diagramas/er.png`.
