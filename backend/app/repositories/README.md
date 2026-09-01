# repositories/

Aqui vive toda la logica de acceso a la base de datos. Los repositorios
son el unico lugar del sistema donde hablamos directamente con PostgreSQL
a traves del ORM.

## Lo que va aqui

- Las consultas a la base de datos (lecturas, escrituras, filtros)
- La logica de paginacion y ordenamiento
- Las operaciones CRUD de cada entidad

## Lo que no va aqui

La logica de negocio no vive aqui. Si necesitamos hacer algo con los
datos despues de leerlos, ese trabajo pertenece al servicio que llamo
al repositorio.

## Como funciona

`base_repository.py` contiene las operaciones comunes (guardar, buscar
por ID, listar, eliminar). Cada repositorio especifico extiende esa base
y agrega las consultas particulares que su entidad necesita.
