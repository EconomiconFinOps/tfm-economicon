# Diseño técnico — JUP-089

## Contexto y decisiones

La composición de alta fidelidad fue aprobada por Paris el 19/10/2026. Se incorpora HTML/CSS/JS propio conservando layout, contenido, espaciados, tipografía y recorrido. No se rescata código HTML/JS de PR106 (cerrada sin merge); sólo recursos binarios originales con atribución y licencias.

1. Aplicación estática independiente apps/landing: Node.js 22+ y biblioteca estándar para construir, probar y servir. Sin framework ni dependencias de producción. La app privada sigue siendo independiente.
2. src/ contiene únicamente la fuente pública; el build copia una lista cerrada de HTML/CSS/JS/logos/fuentes/licencias, rechaza enlaces simbólicos y genera un manifiesto de hashes. Nunca publica el repositorio o variables de entorno. El directorio dist se reemplaza sólo en su ruta fija propia, tras generar correctamente en un temporal hermano.
3. El servidor local sólo sirve archivos del manifiesto bajo dist y una 404 real; no hay fallback SPA, API, cookies, sesiones ni listado de carpetas. Bind por defecto127.0.0.1. Cabeceras CSP, nosniff, referrer y anti-frame; CSP bloquea conexiones y formularios. La política permite estilos inline sólo por los porcentajes estáticos de las ilustraciones, sin entradas del usuario.
4. Sin SITE_ORIGIN el build es local/staging: noindex y robots Disallow:/; sitemap sin URLs públicas ni canonical/og:url inventados. Con SITE_ORIGIN HTTPS raíz válido genera canonical, og:url, og:image absoluta, robots y sitemap del único recurso indexable. Cambiar SITE_ORIGIN sólo altera metadatos, no conexiones ni demo. Despliegue real requiere aprobar dominio y responsable de renovación y configurar HTTPS/cabeceras en el host.
5. Demo y fuentes ilustrativas permanecen simuladas y rotuladas. Menú, tabs y dialog son nativos; modal con cierre accesible, Escape y retorno del foco, navegación de tabs con flechas/Home/End y movimiento reducido. Noscript explica cómo recorrer el contenido sin la demo interactiva.
6. Correcciones ordinarias respecto a la maqueta: contraste de textos secundarios/foco y color lila/índigo de la candidata de anomalía. ADR-0012 y frontend-brand-identity prohíben coral para anomalías. Paris/PM confirmó el 19/10 que aprobar la maqueta no creó esa excepción. No cambia composición, texto o pasos. No hace falta otro ADR: no altera arquitectura privada ni la política de marca.

## Comprobación y operación

Pruebas Node del build/servidor: origen inválido, secretos no incluidos, symlinks, error de build sin pérdida de última salida, métodos/rutas no permitidos, MIME, cabeceras,404 y SEO. Navegador sobre dist a1440/390/320, teclado, foco, tabs/demo, reduced-motion; mediciones locales explícitas sin equivaler a campo o HTTPS público. Nuevo job CI aislado usa Node22 con permisos mínimos y acciones ya pineadas. Checks obligatorios del repositorio se reconcilian con CONTRIBUTING y CI; no se sustituyen por la prueba focal.

Manual apps/landing/README.md y docs/operations/public-landing.md para build, preview, publicación propuesta y rollback por artefacto inmutable. Decisiones de hosting/dominio/destino demo se elevan, sin inferir permisos por preparar el paquete.

## Referencias técnicas consultadas

- [MDN dialog](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog): showModal, cierre y foco.
- [WAI-ARIA tabs](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/): selección y teclado.
- [Google Search, sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap): URLs absolutas del origen elegido, no dominio ficticio.
- [Node.js fs](https://nodejs.org/api/fs.html) y [http](https://nodejs.org/api/http.html): copia explícita y servidor con biblioteca estándar.
- [MDN PerformanceNavigationTiming](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceNavigationTiming): mediciones de laboratorio local, no experiencia real en producción.

## Integración con el workspace

La configuración Turbo específica de apps/landing hereda la raíz, declara SITE_ORIGIN/LANDING_OUT_DIR en build/dev y PORT en dev. Los parámetros entran en el hash y llegan al proceso en modo estricto. La tarea build de landing no usa caché ni outputs relativos: reconstruye siempre el pequeño artefacto, también si el destino es externo. Evita recuperar una salida de otro origen o saltarse la escritura del destino dinámico sin afectar la caché de otras apps. Regresión sobre los planes efectivos y compilación real del consumidor raíz en CI. Referencias: [Package configurations](https://turborepo.dev/docs/reference/package-configurations) y [variables de entorno](https://turborepo.dev/docs/crafting-your-repository/using-environment-variables).
