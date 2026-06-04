# controllers/

Aqui viven los Blueprints de Flask. Cada archivo corresponde a un
dominio de la aplicacion y agrupa las rutas relacionadas con ese dominio.

## Lo que va aqui

- Las rutas HTTP (endpoints) organizadas por Blueprint
- La validacion del formato de la peticion entrante
- La llamada al servicio correspondiente
- La construccion de la respuesta que se devuelve al cliente

## Lo que no va aqui

La logica de negocio no vive en los controladores. Si nos encontramos
escribiendo condiciones complejas o consultas a la base de datos dentro
de un Blueprint, eso pertenece a un servicio o un repositorio.

## Los Blueprints del proyecto

| Archivo | Dominio |
|---------|---------|
| `auth_bp.py` | Registro, login y gestion de sesion |
| `panorama_bp.py` | Tendencias, rankings y datos del dashboard |
| `alerts_bp.py` | Configuracion y gestion de alertas del usuario |
| `admin_bp.py` | Administracion de usuarios y respaldos |
