# Economicon — landing pública (JUP-089)

Sitio estático autónomo para equipos pequeños de ingeniería y finanzas que quieren
entender el gasto Azure con contexto. CTA principal al repositorio público;
recorrido secundario dentro de la página. No hay acceso a la aplicación privada,
API, formularios, cookies ni analítica. Los conceptos y capturas de pruebas están
identificados como simulados.

## Ejecutar

Desde la raíz del repositorio, con Node 22 o posterior:

```sh
node apps/landing/build.mjs
node apps/landing/serve.mjs
```

Abrir `http://127.0.0.1:4179`. El servidor es solo una preview de loopback;
`PORT` permite otro puerto. Con el workspace instalado también se puede usar
`corepack pnpm --filter @finops/landing dev`.

```sh
corepack pnpm --filter @finops/landing lint
corepack pnpm --filter @finops/landing test
corepack pnpm --filter @finops/landing build
```

No necesita instalar dependencias del monorepo para ejecutarse mediante Node o
`npm --prefix apps/landing test`. Su CI usa Node 22 y no accede a los servicios
de la aplicación.

## Publicar

Se publica **solo `apps/landing/dist`**, después de aprobar el origen y hosting.
Por defecto genera `noindex,nofollow`; nunca configura un dominio supuesto.

| Variable de build | Uso |
| --- | --- |
| `PUBLIC_SITE_URL` | Raíz HTTPS del dominio público aprobado; activa canonical, `og:url`, imagen OG absoluta, robots y sitemap. |
| `PUBLIC_VIDEO_URL` | Enlace HTTPS aprobado a una pieza conceptual; no incrusta reproductores ni carga terceros. |
| `PUBLIC_VIDEO_TITLE` | Texto del enlace de vídeo, opcional, máximo 160 caracteres. |

No introducir URLs firmadas, tokens ni endpoints privados en estas variables:
son contenido público. La validación de URL es sintáctica, no prueba propiedad,
DNS, certificados, disponibilidad ni autorización editorial.

El build selecciona archivos explícitos, rechaza enlaces de recursos desconocidos,
scripts, formularios y symlinks, y reemplaza solo el `dist` hermano de `src`.
El servidor devuelve 404 real y no implementa fallback SPA. La preview siempre
envía `X-Robots-Tag: noindex`, incluso al ensayar metadatos públicos.

Ver [publicación y rollback](../../docs/operations/public-landing.md),
[evidencia y límites](../../docs/evidence/JUP-089-validation.md) y
[procedencia de assets](ATTRIBUTIONS.md). `apps/frontend` y sus estilos permanecen
separados; JUP-112 se ocupa de esa aplicación.
