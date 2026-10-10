# JUP-089 — Frontera de la landing pública

## Decisiones

Separar `apps/landing` de la aplicación autenticada. HTML y CSS estáticos bastan
para el recorrido público y permiten publicar exclusivamente un directorio
`dist`, sin backend, proxy, secretos o conexión al entorno de demostración.
Decisión duradera propuesta: [ADR-0018](../../../docs/adr/ADR-0018-public-landing-boundary.md).

El build usa Node 22 y una selección explícita de fuentes públicas. Por defecto
genera una preview no indexable. `PUBLIC_SITE_URL` fija un origen HTTPS público
aprobado para canonical, Open Graph, robots y sitemap; no implica propiedad del
dominio ni despliegue. Las URLs configuradas se validan y escapan. Los metadatos
no se rellenan con nombres de servidores privados ni dominios inventados.

## Identidad y contenido

JUP-112 y el dossier definen índigo, violeta para CTA, lila, coral, blanco roto,
Space Grotesk e Inter. La landing adopta esa marca sin importar estilos del
frontend privado. Su audiencia son equipos pequeños de ingeniería y finanzas;
el mensaje es entender el gasto Azure con contexto. CTA principal al repositorio
público, secundaria al recorrido explicado en la propia página.

El mockup del dossier es un concepto no interactivo con datos simulados; las
capturas de pruebas históricas se etiquetan con fecha y API simulada. La presencia
de código integrado no demuestra disponibilidad pública, ahorro real o aceptación
del recorrido generativo. El vídeo conceptual solo se enlaza cuando exista una
URL pública revisada; la ausencia de publicación se expresa como tal.

## Publicación y dependencias

El sitio se sirve en la raíz de un origen independiente, con 404 HTTP real y
cabeceras de seguridad. No se modifica el Compose de aplicación. Publicación
pendiente de dominio/responsable de renovación, hosting, HTTPS, material audiovisual
aprobado y contraste de M4/M5. La preview local y los dobles de prueba prueban la
landing, no esas dependencias. Sin analítica, formularios ni consentimiento ficticio.

## Verificación

Pruebas Node de build, URLs, ausencia de fuentes privadas y servidor; comprobación
en navegador de enlaces/anclas, teclado, responsive, imágenes, 404 y peticiones;
medición Lighthouse local y evidencia por criterio. Las revisiones humanas
exigidas por CONTRIBUTING siguen pendientes y no se sustituyen con subagentes.
