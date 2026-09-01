# Git en el dia a dia

Esta guia cubre los comandos de Git que usamos en SkillStat. No asume conocimiento previo. Si ya dominas Git puedes usarla como referencia rapida.

## Como funciona Git en este proyecto

Git guarda el historial de todos los cambios que hacemos al codigo. Cada vez que guardamos un cambio con `commit` quedamos un registro de que cambio, quien lo hizo y cuando.

Las ramas nos permiten trabajar en algo nuevo sin afectar lo que ya funciona. Cuando terminamos, integramos nuestro trabajo a `develop` a traves de un Pull Request en GitHub.

## Los comandos que mas usamos

**Ver en que rama estamos y que archivos cambiamos:**
```bash
git status
```

**Ver el historial de commits:**
```bash
git log --oneline
```

**Traer los cambios mas recientes del repositorio remoto:**
```bash
git pull origin develop
```

**Crear una rama nueva desde develop:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-de-la-tarea
```

**Guardar nuestros cambios en un commit:**
```bash
git add .
git commit -m "feat(scope): descripcion del cambio"
```

**Subir nuestra rama al repositorio remoto:**
```bash
git push origin feature/nombre-de-la-tarea
```

**Actualizar nuestra rama con los ultimos cambios de develop:**
```bash
git fetch origin
git rebase origin/develop
```

**Cambiar de rama:**
```bash
git checkout nombre-de-la-rama
```

**Ver todas las ramas disponibles:**
```bash
git branch -a
```

## El flujo completo de una tarea

```bash
# Empezamos siempre desde develop actualizado
git checkout develop
git pull origin develop

# Creamos nuestra rama
git checkout -b feature/mi-tarea

# Trabajamos... hacemos cambios... y guardamos
git add .
git commit -m "feat(modulo): descripcion"

# Si develop recibio nuevos cambios mientras trabajabamos
git fetch origin
git rebase origin/develop

# Subimos nuestra rama
git push origin feature/mi-tarea

# Desde GitHub abrimos el Pull Request hacia develop
```

## Lo que no hacemos

- No hacemos commits directamente sobre `develop` o `main`.
- No usamos `git push --force` en ramas compartidas.
- No hacemos merge de nuestro propio Pull Request.
- No subimos el archivo `.env` ni ninguna credencial al repositorio.

## Cuando algo sale mal

Si nos equivocamos en el mensaje de un commit antes de subir los cambios:
```bash
git commit --amend -m "feat(scope): mensaje corregido"
```

Si queremos deshacer el ultimo commit pero conservar los cambios:
```bash
git reset --soft HEAD~1
```

Si tenemos dudas sobre algo que no esta en esta guia lo preguntamos antes de intentar comandos desconocidos.
