# Inventario Frontend — SkillStat
**Generado:** 2026-06-19 (hora local CDT, UTC-6)  
**Operación:** Solo lectura. Cero archivos modificados dentro de `frontend/`. Cero comandos Git ejecutados. Un único archivo nuevo creado (este documento).  
**Metodología de clasificación:**
- **EMPTY** → tras eliminar líneas en blanco y líneas de comentario puro, no queda ninguna línea de contenido real.
- **POPULATED** → queda al menos una línea de contenido real; se reporta el conteo exacto.

---

## Árbol completo de `frontend/`

```
frontend/
├── README.md
├── assets/
│   ├── css/
│   │   ├── main.css
│   │   ├── base/
│   │   │   ├── _reset.css
│   │   │   ├── _typography.css
│   │   │   ├── _utilities.css
│   │   │   └── _variables.css
│   │   ├── components/
│   │   │   ├── _alerts.css
│   │   │   ├── _buttons.css
│   │   │   ├── _cards.css
│   │   │   ├── _carousel.css
│   │   │   ├── _charts.css
│   │   │   ├── _footer.css
│   │   │   ├── _forms.css
│   │   │   ├── _navbar.css
│   │   │   ├── _tables.css
│   │   │   └── _theme-toggle.css
│   │   ├── layouts/
│   │   │   ├── _containers.css
│   │   │   └── _grid.css
│   │   └── pages/
│   │       ├── _admin.css
│   │       ├── _alertas.css
│   │       ├── _auth.css
│   │       ├── _index.css
│   │       └── _panorama.css
│   ├── images/
│   │   ├── brand/
│   │   │   └── .gitkeep           ← carpeta vacía (sin skillstat-logo.svg)
│   │   └── icons/
│   │       └── .gitkeep           ← carpeta vacía
│   └── js/
│       ├── api/
│       │   ├── admin.api.js
│       │   ├── alertas.api.js
│       │   ├── auth.api.js
│       │   ├── client.js
│       │   └── panorama.api.js
│       ├── components/
│       │   ├── carousel.init.js
│       │   ├── chart.init.js
│       │   ├── icons.init.js
│       │   ├── map.init.js
│       │   └── navbar.js
│       ├── pages/
│       │   ├── admin.js
│       │   ├── alertas.js
│       │   ├── comparar.js
│       │   ├── index.js
│       │   └── panorama.js
│       └── utils/
│           ├── auth.utils.js
│           ├── formatters.js
│           └── validators.js
└── views/
    ├── alertas.html
    ├── comparar.html
    ├── index.html
    ├── panorama.html
    ├── register.html
    ├── admin/
    │   ├── respaldos.html
    │   └── usuarios.html
    └── errors/
        ├── 404.html
        └── 500.html
```

---

## Verificación puntual — Logo SVG

| Ruta | Existe |
|------|--------|
| `assets/images/brand/skillstat-logo.svg` | **NO** — la carpeta solo contiene `.gitkeep` |

> ⚠️ `index.html` referencia el logo en dos lugares (`<img src="../assets/images/brand/skillstat-logo.svg">`). El archivo no existe; la imagen no renderizará.

---

## CSS — `assets/css/`

### `main.css` (punto de entrada único)

| Campo | Valor |
|-------|-------|
| Ruta relativa | `assets/css/main.css` |
| Clasificación | **POPULATED** |
| Líneas de contenido real | **12** (las 19 de comentario/vacías se filtran; quedan los 12 `@import` activos: líneas 4-7, 10-12, 17-19, 22 y 27; las `@import` comentadas se descartan) |
| Referenciado desde | `views/index.html` línea 23: `<link rel="stylesheet" href="../assets/css/main.css" />` |
| Última modificación | 2026-06-18 22:20:53 |

**`@import` activos en `main.css`:**
```
@import url("base/_variables.css");      ← línea 4
@import url("base/_reset.css");          ← línea 5
@import url("base/_typography.css");     ← línea 6
@import url("base/_utilities.css");      ← línea 7
@import url('components/_navbar.css');   ← línea 10
@import url('components/_buttons.css');  ← línea 11
@import url('components/_cards.css');    ← línea 12
@import url('components/_carousel.css'); ← línea 17
@import url('components/_footer.css');   ← línea 18
@import url('components/_theme-toggle.css'); ← línea 19
@import url('layouts/_containers.css');  ← línea 22
@import url('pages/_index.css');         ← línea 27
```

**`@import` comentados (no activos):**
- `components/_forms.css`, `components/_charts.css`, `components/_badges.css`, `components/_alerts.css`
- `layouts/_grid.css`, `layouts/_navbar-layout.css`
- `pages/_panorama.css`, `pages/_auth.css`, `pages/_alertas.css`, `pages/_comparar.css`, `pages/_admin.css`

---

### Subcarpeta `base/`

| Archivo | Clasificación | Líneas reales | En `main.css` | Última modificación |
|---------|--------------|---------------|---------------|---------------------|
| `base/_variables.css` | **POPULATED** | 86 | Sí — `@import url("base/_variables.css")` línea 4 | 2026-06-18 22:00:52 |
| `base/_reset.css` | **POPULATED** | 71 | Sí — `@import url("base/_reset.css")` línea 5 | 2026-06-18 15:43:58 |
| `base/_typography.css` | **POPULATED** | 82 | Sí — `@import url("base/_typography.css")` línea 6 | 2026-06-18 15:51:41 |
| `base/_utilities.css` | **POPULATED** | 11 | Sí — `@import url("base/_utilities.css")` línea 7 | 2026-06-18 19:22:15 |

> **Nota de conteo `_variables.css`:** 110 líneas totales. Se filtran: 0 líneas de comentario puro + 24 líneas en blanco → quedan 86 líneas de contenido real.  
> **Nota `_reset.css`:** 95 líneas totales. Se filtran: 5 líneas de comentario puro + ~19 líneas en blanco → 71 reales.  
> **Nota `_typography.css`:** 107 líneas totales. Se filtran: 8 líneas de comentario puro + 17 en blanco → 82 reales.  
> **Nota `_utilities.css`:** 15 líneas totales. Se filtran: 3 líneas de comentario puro + 1 en blanco → 11 reales.

---

### Subcarpeta `components/`

| Archivo | Clasificación | Líneas reales | En `main.css` (estado) | Última modificación |
|---------|--------------|---------------|------------------------|---------------------|
| `components/_alerts.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |
| `components/_buttons.css` | **POPULATED** | 36 | Sí — `@import url('components/_buttons.css')` línea 11 | 2026-06-18 21:36:53 |
| `components/_cards.css` | **POPULATED** | 118 | Sí — `@import url('components/_cards.css')` línea 12 | 2026-06-18 22:45:16 |
| `components/_carousel.css` | **POPULATED** | 39 | Sí — `@import url('components/_carousel.css')` línea 17 | 2026-06-18 22:07:35 |
| `components/_charts.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |
| `components/_footer.css` | **POPULATED** | 56 | Sí — `@import url('components/_footer.css')` línea 18 | 2026-06-18 22:20:49 |
| `components/_forms.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |
| `components/_navbar.css` | **POPULATED** | 34 | Sí — `@import url('components/_navbar.css')` línea 10 | 2026-06-18 21:25:52 |
| `components/_tables.css` | **EMPTY** | 0 | Comentado (inactivo) — línea 17 | 2026-06-03 15:55:43 |
| `components/_theme-toggle.css` | **POPULATED** | 41 | Sí — `@import url('components/_theme-toggle.css')` línea 19 | 2026-06-18 21:25:23 |


> **Nota de conteo:**
> - `_buttons.css`: 47 líneas totales → −1 comentario puro − 10 en blanco = 36 reales
> - `_cards.css`: 150 líneas totales → −2 comentarios puros − 30 en blanco = 118 reales
> - `_carousel.css`: 47 líneas totales → −1 comentario puro − 7 en blanco = 39 reales
> - `_footer.css`: 74 líneas totales → −1 comentario puro − 17 en blanco = 56 reales
> - `_navbar.css`: 43 líneas totales → −1 comentario puro − 8 en blanco = 34 reales
> - `_theme-toggle.css`: 50 líneas totales → −1 comentario puro − 8 en blanco = 41 reales

---

### Subcarpeta `layouts/`

| Archivo | Clasificación | Líneas reales | En `main.css` (estado) | Última modificación |
|---------|--------------|---------------|------------------------|---------------------|
| `layouts/_containers.css` | **POPULATED** | 16 | Sí — `@import url('layouts/_containers.css')` línea 22 | 2026-06-18 21:26:04 |
| `layouts/_grid.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |

> **Nota `_containers.css`:** 21 líneas totales → −1 comentario puro − 4 en blanco = 16 reales.

---

### Subcarpeta `pages/`

| Archivo | Clasificación | Líneas reales | En `main.css` (estado) | Última modificación |
|---------|--------------|---------------|------------------------|---------------------|
| `pages/_admin.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |
| `pages/_alertas.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |
| `pages/_auth.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |
| `pages/_index.css` | **POPULATED** | 68 | Sí — `@import url('pages/_index.css')` línea 27 | 2026-06-18 22:53:41 |
| `pages/_panorama.css` | **EMPTY** | 0 | Comentado (no activo) | 2026-06-03 15:55:43 |

> **Nota `_index.css`:** 85 líneas totales → −1 comentario puro − 16 en blanco = 68 reales.

---

## JavaScript — `assets/js/`

### Subcarpeta `api/`

| Archivo | Clasificación | Líneas reales | Referenciado en HTML | Última modificación |
|---------|--------------|---------------|----------------------|---------------------|
| `api/admin.api.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `api/alertas.api.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `api/auth.api.js` | **EMPTY** | 0 | `views/index.html` línea 397: `<script src="../assets/js/api/auth.api.js">` | 2026-06-03 15:55:43 |
| `api/client.js` | **EMPTY** | 0 | `views/index.html` línea 396: `<script src="../assets/js/api/client.js">` | 2026-06-03 15:55:43 |
| `api/panorama.api.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |

---

### Subcarpeta `components/`

| Archivo | Clasificación | Líneas reales | Referenciado en HTML | Última modificación |
|---------|--------------|---------------|----------------------|---------------------|
| `components/carousel.init.js` | **POPULATED** | 63 | `views/index.html` línea 401: `<script src="../assets/js/components/carousel.init.js">` | 2026-06-18 22:09:57 |
| `components/chart.init.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `components/icons.init.js` | **POPULATED** | 5 | `views/index.html` línea 399: `<script src="../assets/js/components/icons.init.js">` | 2026-06-18 21:23:57 |
| `components/map.init.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `components/navbar.js` | **POPULATED** | 20 | `views/index.html` línea 400: `<script src="../assets/js/components/navbar.js">` | 2026-06-18 21:24:31 |

> **Nota de conteo:**
> - `carousel.init.js`: 81 líneas totales → −1 comentario de línea (`//`) − 17 en blanco = 63 reales
> - `icons.init.js`: 7 líneas totales → −1 comentario de línea − 1 en blanco = 5 reales
> - `navbar.js`: 26 líneas totales → −1 comentario de línea − 5 en blanco = 20 reales

---

### Subcarpeta `pages/`

| Archivo | Clasificación | Líneas reales | Referenciado en HTML | Última modificación |
|---------|--------------|---------------|----------------------|---------------------|
| `pages/admin.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `pages/alertas.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `pages/comparar.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `pages/index.js` | **EMPTY** | 0 | `views/index.html` línea 402: `<script src="../assets/js/pages/index.js">` | 2026-06-18 16:09:06 |
| `pages/panorama.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |

> **Nota `pages/index.js`:** Contiene solo una línea de comentario `//` + una línea en blanco. Clasificado EMPTY porque no queda línea de código real después del filtro. Está referenciado desde `index.html` pero no ejecuta nada.

---

### Subcarpeta `utils/`

| Archivo | Clasificación | Líneas reales | Referenciado en HTML | Última modificación |
|---------|--------------|---------------|----------------------|---------------------|
| `utils/auth.utils.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |
| `utils/formatters.js` | **EMPTY** | 0 | `views/index.html` línea 395: `<script src="../assets/js/utils/formatters.js">` | 2026-06-03 15:55:43 |
| `utils/validators.js` | **EMPTY** | 0 | no referenciado en ningún HTML | 2026-06-03 15:55:43 |

---

## HTML — `views/`

### `views/index.html`

| Campo | Valor |
|-------|-------|
| Clasificación | **POPULATED** |
| Líneas totales del archivo | **405** |
| Líneas de contenido real | **310** (405 − ~60 líneas de comentario HTML completo − ~35 líneas en blanco) |
| Última modificación | 2026-06-18 23:07:12 |

**Etiquetas estructurales de primer nivel:**

| Etiqueta | `id` / `class` / atributos relevantes |
|----------|---------------------------------------|
| `<header class="site-header" role="banner">` | class=`site-header`, role=`banner` |
| `<nav class="navbar" aria-label="Navegación principal">` | class=`navbar`, aria-label=`Navegación principal` |
| `<main>` | sin atributos |
| `<section class="hero" aria-labelledby="hero-heading">` | class=`hero`, aria-labelledby=`hero-heading` |
| `<section class="carousel-section" aria-label="Métricas destacadas del mercado">` | class=`carousel-section`, aria-label=`Métricas destacadas del mercado` |
| `<section class="cta-section" aria-label="Acciones principales">` | class=`cta-section`, aria-label=`Acciones principales` |
| `<section class="value-props" aria-labelledby="value-props-heading">` | class=`value-props`, aria-labelledby=`value-props-heading` |
| `<section class="panorama-preview" aria-labelledby="preview-heading">` | class=`panorama-preview`, aria-labelledby=`preview-heading` |
| `<footer class="site-footer" role="contentinfo">` | class=`site-footer`, role=`contentinfo` |
| `<nav class="footer__legal" aria-label="Enlaces legales">` | class=`footer__legal`, aria-label=`Enlaces legales` |

**Scripts cargados en `index.html` (orden en el body):**
```
línea 395: <script src="../assets/js/utils/formatters.js">
línea 396: <script src="../assets/js/api/client.js">
línea 397: <script src="../assets/js/api/auth.api.js">
línea 398: <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js">  ← CDN externo
línea 399: <script src="../assets/js/components/icons.init.js">
línea 400: <script src="../assets/js/components/navbar.js">
línea 401: <script src="../assets/js/components/carousel.init.js">
línea 402: <script src="../assets/js/pages/index.js">
```

---

### Resto de vistas — todas EMPTY

| Archivo | Clasificación | Líneas reales | Última modificación |
|---------|--------------|---------------|---------------------|
| `views/alertas.html` | **EMPTY** | 0 | 2026-06-03 15:55:43 |
| `views/comparar.html` | **EMPTY** | 0 | 2026-06-03 15:55:43 |
| `views/panorama.html` | **EMPTY** | 0 | 2026-06-17 07:17:46 |
| `views/register.html` | **EMPTY** | 0 | 2026-06-03 15:55:43 |
| `views/admin/respaldos.html` | **EMPTY** | 0 | 2026-06-03 15:55:43 |
| `views/admin/usuarios.html` | **EMPTY** | 0 | 2026-06-03 15:55:43 |
| `views/errors/404.html` | **EMPTY** | 0 | 2026-06-03 15:55:43 |
| `views/errors/500.html` | **EMPTY** | 0 | 2026-06-03 15:55:43 |

> **Nota `panorama.html`:** Tiene una fecha de modificación distinta (2026-06-17) pero el contenido es una única línea de comentario HTML. Clasificado EMPTY.

---

## Resumen ejecutivo

### Conteos globales

| Categoría | Total archivos | POPULATED | EMPTY |
|-----------|---------------|-----------|-------|
| CSS (`.css`) | 22 | **13** | **9** |
| JS (`.js`) | 18 | **3** | **15** |
| HTML (`.html`) | 9 | **1** | **8** |
| **Total** | **49** | **17** | **32** |

### Archivos POPULATED — lista consolidada

| Ruta relativa | Líneas reales | Última modificación |
|---------------|---------------|---------------------|
| `assets/css/main.css` | 12 | 2026-06-18 22:20:53 |
| `assets/css/base/_variables.css` | 86 | 2026-06-18 22:00:52 |
| `assets/css/base/_reset.css` | 71 | 2026-06-18 15:43:58 |
| `assets/css/base/_typography.css` | 82 | 2026-06-18 15:51:41 |
| `assets/css/base/_utilities.css` | 11 | 2026-06-18 19:22:15 |
| `assets/css/components/_buttons.css` | 36 | 2026-06-18 21:36:53 |
| `assets/css/components/_cards.css` | 118 | 2026-06-18 22:45:16 |
| `assets/css/components/_carousel.css` | 39 | 2026-06-18 22:07:35 |
| `assets/css/components/_footer.css` | 56 | 2026-06-18 22:20:49 |
| `assets/css/components/_navbar.css` | 34 | 2026-06-18 21:25:52 |
| `assets/css/components/_theme-toggle.css` | 41 | 2026-06-18 21:25:23 |
| `assets/css/layouts/_containers.css` | 16 | 2026-06-18 21:26:04 |
| `assets/css/pages/_index.css` | 68 | 2026-06-18 22:53:41 |
| `assets/js/components/carousel.init.js` | 63 | 2026-06-18 22:09:57 |
| `assets/js/components/icons.init.js` | 5 | 2026-06-18 21:23:57 |
| `assets/js/components/navbar.js` | 20 | 2026-06-18 21:24:31 |
| `views/index.html` | 310 | 2026-06-18 23:07:12 |

### Anomalías detectadas

| # | Tipo | Detalle |
|---|------|---------|
| 1 | **Imagen faltante** | `assets/images/brand/skillstat-logo.svg` no existe. `index.html` lo referencia en líneas 37 y 362. La carpeta `brand/` solo contiene `.gitkeep`. |
| 2 | **JS huérfano cargado en HTML pero EMPTY** | `utils/formatters.js`, `api/client.js`, `api/auth.api.js`, `pages/index.js` están en el `<script>` stack de `index.html` pero no contienen código real. Se cargan, parsean y ejecutan sin efecto. |
| 3 | **CSS huérfano (resuelto)** | `components/_tables.css` fue agregado al bloque de `@import` comentados de `main.css` en la ronda de limpieza. Sigue **EMPTY** de contenido, pendiente de implementación real, pero ya no es huérfano de referencia. |
| 4 | **CSS comentado pero POPULATED** | Ninguno — todos los archivos con `@import` comentado son EMPTY, lo cual es consistente. |
| 5 | **Dependencias JS no cubiertas** | `carousel.init.js` usa `IntersectionObserver` y espera `[data-carousel]` en el DOM. `navbar.js` espera `[data-theme-toggle]`. Ambas dependencias existen en `index.html`. La dependencia de Lucide (CDN) se carga antes de `icons.init.js` — orden correcto. |
| 6 | **Vistas sin HTML** | 8 de 9 vistas `.html` son EMPTY. Ninguna vista más allá de `index.html` puede renderizarse. |
| 7 | **`panorama.html` con fecha diferente** | Modificado el 2026-06-17 (diferente del lote del 2026-06-03), pero el contenido sigue siendo solo un comentario. Posible edición menor sin contenido real. |

---

*Fin del inventario. Ningún archivo dentro de `frontend/` fue modificado durante esta operación.*
