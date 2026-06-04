# frontend/

Aqui vive todo lo que el usuario ve y con lo que interactua: las vistas
HTML, los estilos CSS y la logica JavaScript del cliente.

## Estructura

```
frontend/
├── assets/
│   ├── css/      Estilos organizados por funcion
│   ├── js/       Logica del cliente organizada por responsabilidad
│   └── images/   Iconos y recursos graficos
└── views/        Un archivo HTML por cada pantalla de la aplicacion
```

## Como organizamos los estilos

- `css/base/` - variables globales, reset y tipografia. Lo que aplica a toda la app.
- `css/components/` - estilos de piezas reutilizables: botones, tarjetas, graficas.
- `css/layouts/` - rejillas y contenedores estructurales.
- `css/pages/` - estilos especificos de cada pantalla.
- `css/main.css` - punto de entrada que importa todo lo anterior.

## Como organizamos el JavaScript

- `js/api/` - funciones que se comunican con la API del backend. Una por dominio.
- `js/components/` - inicializacion de componentes visuales como Chart.js o el mapa.
- `js/pages/` - logica especifica de cada pantalla.
- `js/utils/` - funciones compartidas: formateo de numeros, validacion, manejo del token.

## Las vistas

Cada pantalla tiene su propio archivo HTML en `views/`. El archivo
`views/panorama.html` es el dashboard principal del sistema.

No ponemos logica de backend aqui. No accedemos a la base de datos
desde el frontend. Todo pasa por la API REST del backend.
