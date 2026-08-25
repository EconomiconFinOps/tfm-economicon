# Uso de Turborepo en este proyecto

## 1. Que es Turborepo

Turborepo es una herramienta para trabajar mejor con un **monorepo**.

Un monorepo es un repositorio donde viven varias aplicaciones o paquetes juntos. En este proyecto tenemos varios:

- `apps/frontend`
- `apps/backend`
- `apps/processor`
- `packages/shared-config`

Sin una herramienta como Turbo, tendriamos que entrar en cada carpeta y ejecutar comandos uno por uno. Con Turborepo podemos lanzar tareas desde la raiz y dejar que el sistema coordine todo.

## 2. Por que lo usamos

Lo usamos porque este repo no tiene una sola app. Tiene varias partes que forman un sistema completo:

- un frontend
- un backend
- un processor
- paquetes compartidos

Turborepo ayuda a resolver problemas muy comunes en este tipo de repositorios:

- Ejecutar comandos para varias apps desde un solo sitio.
- Mantener una forma consistente de trabajar para todo el equipo.
- Entender dependencias entre tareas.
- Ahorrar tiempo reutilizando resultados cuando aplica.

En otras palabras: hace que trabajar con muchas apps en el mismo repo sea mas simple y ordenado.

## 3. Que funciones cumple en este repo

En la raiz del proyecto hay un archivo llamado [turbo.json](/C:/Repositorios/tfm-economicon/turbo.json). Ese archivo le dice a Turbo que tareas existen y como debe tratarlas.

En este repo Turbo coordina principalmente estas tareas:

- `dev`
- `build`
- `lint`
- `test`
- `docker:build`

Y en el [package.json](/C:/Repositorios/tfm-economicon/package.json) de la raiz esas tareas se ejecutan asi:

```json
"dev": "turbo run dev --parallel",
"build": "turbo run build",
"lint": "turbo run lint",
"test": "turbo run test",
"docker:build": "turbo run docker:build"
```

Eso significa que cuando ejecutas un comando en la raiz, Turbo busca que apps tienen ese script y lo lanza por ti.

## 4. Como entiende Turbo este workspace

El archivo [pnpm-workspace.yaml](/C:/Repositorios/tfm-economicon/pnpm-workspace.yaml) indica que forman parte del workspace estas rutas:

- `apps/*`
- `packages/*`

Eso le da contexto al monorepo. Gracias a eso, Turbo sabe que debe mirar dentro de `apps` y `packages` para encontrar proyectos y scripts.

## 5. Que hace cada tarea

### `pnpm dev`

Sirve para arrancar el entorno de desarrollo.

En este repo, al ejecutar:

```powershell
pnpm dev
```

Turbo lanza el script `dev` de los proyectos que lo tengan definido. Ahora mismo eso incluye:

- `apps/frontend`
- `apps/backend`
- `apps/processor`

En la practica, esto evita abrir tres terminales y arrancar cada servicio manualmente.

### `pnpm build`

Sirve para construir los proyectos para un entorno de produccion o para comprobar que compilan correctamente.

```powershell
pnpm build
```

En `turbo.json`, la tarea `build` tiene esta parte:

```json
"dependsOn": ["^build"]
```

Esto significa, de forma simple, que si un proyecto depende de otro, Turbo intenta construir antes las dependencias necesarias.

Tambien se declaran salidas como:

- `dist/**`
- `build/**`

Esto ayuda a Turbo a saber que archivos genera una build.

### `pnpm lint`

Sirve para revisar estilo, errores simples o problemas de calidad en el codigo.

```powershell
pnpm lint
```

Turbo ejecuta el `lint` de cada app que lo tenga definido.

### `pnpm test`

Sirve para ejecutar tests desde la raiz.

```powershell
pnpm test
```

Turbo lanza los tests de los proyectos que tengan script `test`.

### `pnpm docker:build`

Sirve para construir las imagenes Docker declaradas por cada app.

```powershell
pnpm docker:build
```

Es util cuando quieres preparar varias imagenes sin ir carpeta por carpeta.

## 6. Por que `dev` va en paralelo

En [turbo.json](/C:/Repositorios/tfm-economicon/turbo.json), `dev` esta definido asi:

```json
"dev": {
  "cache": false,
  "persistent": true
}
```

Y en el script de la raiz se usa:

```json
"dev": "turbo run dev --parallel"
```

Esto se hace porque `frontend`, `backend` y `processor` son procesos que deben quedarse corriendo mientras desarrollas.

- `persistent: true` indica que son procesos largos, no tareas que terminan rapido.
- `--parallel` permite levantar varios servicios a la vez.
- `cache: false` evita tratar el modo desarrollo como una tarea cacheable, porque no tiene sentido reutilizar ese resultado.

## 7. Cuando te conviene usar Turbo

Usa Turbo cuando quieras trabajar desde la raiz del proyecto y coordinar varias apps al mismo tiempo.

Ejemplos comunes:

- Quieres levantar todo el entorno: `pnpm dev`
- Quieres probar que todo construye bien: `pnpm build`
- Quieres pasar revisiones de calidad en todo el repo: `pnpm lint`
- Quieres lanzar tests de todos los proyectos: `pnpm test`

## 8. Cuando no hace falta usar Turbo

No siempre necesitas Turbo.

Si solo vas a trabajar en una aplicacion concreta, puedes entrar en su carpeta y ejecutar sus scripts directamente.

Ejemplo:

```powershell
Set-Location apps/frontend
pnpm dev
```

Eso puede ser util si solo quieres tocar la interfaz y no necesitas arrancar todo el sistema.

## 9. Flujo recomendado para alguien junior en este repo

Si estas empezando, una forma simple de trabajar es esta:

1. Instala dependencias del workspace:

```powershell
pnpm install
```

2. Si vas a usar los servicios Python, prepara sus dependencias segun el README del repo.

3. Desde la raiz, arranca todo:

```powershell
pnpm dev
```

4. Haz tus cambios.

5. Antes de dar algo por bueno, ejecuta:

```powershell
pnpm lint
pnpm test
```

6. Si quieres comprobar compilacion o empaquetado:

```powershell
pnpm build
```

## 10. Resumen rapido

Turborepo en este proyecto sirve para coordinar varias apps desde un solo punto.

Sus beneficios principales aqui son:

- menos trabajo manual
- una forma unica de ejecutar tareas
- mejor organizacion del monorepo
- facilidad para levantar todo el sistema

Si recuerdas una sola idea, que sea esta:

**Turbo no sustituye a tus apps. Turbo las organiza y las ejecuta de forma coordinada.**
