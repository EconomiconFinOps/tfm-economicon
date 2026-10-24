JUP: JUP-140
Trello: https://trello.com/c/rXLyK4g4

## Context and approval

Diseño v2 aprobado: landing-video-app-config-20261023/preanalisis-bm0/v2-docker-compose/diseno-tecnico-propuesto.md, SHA25651c3d34b2898450cb8ef28f79a2df76e2a1b69490759cf581b98b735ebfaace0. Este documento prepara su traslado al checkout autorizado, no lo sustituye ni cambia alcance. Aplicar la frontera de despliegue de ADR-0015-local-compose-deployment-boundary.md; no modificar su estado por integrar la landing.

## Decisions

1. Imagen Node22 multietapa por digest, build una vez y runtime sin construir. Serve verifica bytes del dist. El entrypoint no ejecuta --build, pnpm ni instala dependencias. Respetar el grafo actual serve→build/security para no omitir módulos necesarios.
2. Servicio landing en Compose general sin perfil/servidor manual obligatorio. Puerto interno8080 y hostloopback8088 configurable, redlanding-public; sin backend/DB/Grafana dependencies, credenciales, socket o mounts privados; único bind público dedicado RO ../landing-public-media→/landing/public-media. USER no-root, init/read_only/no-new-privileges y healthz local. Reconciliar ejemplos, diagnóstico/CD, topología y recuentos con la base vigente; no cambiar recursos compartidos.
3. Configuración al arrancar de sólo dos valores. Recurso runtime-config.js same-origin, GET/HEAD JavaScript/nosniff/no-store, sin ETag304. SerializaciónJSON y esquema cerrado. Datos ausentes/inválidos muestran estado neutral y deshabilitan sólo el destino afectado. No env completo, .env, tokens, URLs firmadas o fetch del destino desde Node.
4. HTTPS público normalizado, acotado y sin userinfo/controles/hostlocal/IP/puerto no estándar. Aceptar únicamente parámetros públicos, rechazar credenciales. Preservar HTTPS público como enlace alternativo. Sólo vídeo añade /media/nombre.mp4 acotado, sin consultas, fragmentos, traversal o codificación de separadores; exactamente dos campos públicos. El filtro no certifica todos los secretos: ambos valores se declaran públicos por contrato.
5. Cliente defer en orden, asignación href/src sin innerHTML de env. Composición aprobada clara/oscura, vídeo nativo prominente y único acceso app en cabecera, también móvil. Autoplay inicial muted/playsinline y controles; capturar rechazo de play() para dejar acción manual. Ningún evento de tema/scroll/carga reanuda una pausa voluntaria. Sonido sólo con acción explícita. HTTPS de visor queda sólo como enlace, sin petición automática al proveedor. CSP existente se conserva; media del mismo origen ya permitida por default-src self.
6. Directorio público dedicado fuera de Git/imagen, bind RO en Compose GENERAL. Manifiesto cerrado version/files y name/mimeType/bytes/sha256, máximo16 entradas/16KiB; sólo vídeo seleccionado, hasta50MiB. Rechazo de symlinks/esquema/MIME/tamaño/SHA/ftyp antes de exponer ruta. Lectura acotada y snapshot en memoria verificado al arrancar; RO del host no equivale a inmutabilidad. Fallo deshabilita sólo media. GET/HEAD, single Range206/416; ignorar Range para HEAD/unidad desconocida/multipart, If-Range sin validador no coincide. Ruta exacta sin consultas, rutas codificadas, listados o archivos no seleccionados. Perspectivas mantienen etiquetas simuladas y la aplicación requiere acceso propio; no navegar Access.
7. Misma imagen A→B→A: cambiar env y recrear sólo landing sin build/pull/deps; comprobar imageID/assets, nuevo containerID y estabilidad del resto. Restart no aplica nuevos valores. SITE_ORIGIN sigue build-time por SEO y es ajeno al cambio runtime de enlaces.

## Risks and limits

Drive tiene permiso de compartir según PM; reproducción anónima/embebida, captions y transcripción no acreditados. No declarar PASS por iframe.load. La decisión UX R3 exige reproducción dentro del panel; si el proveedor la impide, registrar evidencia y opciones al PM. El fallback no satisface ese criterio nuevo. Digest concreto Node22, puerto libre y valores finales de recursos se verifican en el entorno autorizado. Nuevos cambios materiales se elevan; detalles ordinarios aprobados no requieren microautorización.

## Verification strategy

Casos focales configuración/serialización/rutas/caché; tests existentes landing/build/server/Turbo y consumidores Compose/CD afectados. Docker real aislado y navegador para vídeo, accesibilidad y configuración; sin modelos/gasto ni ensayos ajenos. Revisor y Validador distintos evalúan candidato fijo con guardas originales PM antes de mostrarse resultados a Paris. Este plan no acredita pruebas realizadas.

## Extensión mínima aprobada tras R1 —23/10/2026

El arranque general original falla en tempfile del processor; su código y su imagen no cambian. Paris autoriza declarar en Compose tmpfs /tmp:uid=10001,gid=10001,mode=0700, coherente con USER economicon/uid10001 del Dockerfile existente. La propiedad exacta del montaje fallido no fue medida y no se inventa; se medirán los permisos efectivos de la corrección. Mantener read_only/no-new-privileges y probar arranque general sin suplemento tmpfs, salud y A/B/A de landing. Topología comprueba destino y propietario/mode explícitos. El estado y los fallos R1 permanecen, con nuevas guardas antes de reevaluar.

## Corrección UX aprobada R3

Un único destino app en cabecera, accesible a320/390px; aviso breve asociado y error sólo si falta/fracasa configuración. Hero sin columna de botones redundantes; panel de vídeo entre introducción e ilustraciones. Cierre conduce al contenido/recursos. Se conserva la carga del proveedor sólo por acción explícita y las protecciones originales. No atribuir reproducción a load o a una miniatura. El código/contrato de runtime, Compose y tmpfs no se rediseñan. Probar sólo estructura/estados/interacciones afectadas, vídeo real y cambio de dos URLs en la misma imagen R3; los globales previos sólo pueden ratificarse por los evaluadores con análisis de impacto. No repetirlos por rutina.

## Diseño aprobado posterior y traspaso

La ampliación visual y suministro local, aceptadas expresamente por Paris el23/10, sustituyen las decisiones históricas de vídeo sólo bajo clic y composición anterior. Se conserva la propuesta externa por identidad; no se copia código/media comercial de la referencia. Modos claro/oscuro siguen preferencia inicial y selección explícita propia; movimiento CSS tiene pausa y reduce conservado, ensayo interactivo dispensado.

Traspaso: directorio externo contiene sólo MP4 aprobado y manifiesto real de nombre/MIME/bytes/SHA; la imagen inicial es separada de medios/configuración. El operador recibe imagen/ref inmutable realmente disponible y directorio, monta la carpeta hermana por Compose GENERAL, verifica SHA/HTTP/reproducción, y cambia/revierte medios o destinos recreando sólo landing sin build/pull. No se inventa hostname ni se presenta imagen local como publicada. Distribución, despliegue externo y aprobación final quedan pendientes.


## R4 — factual description and existing origin wiring

src/llms.txt is an explicit PUBLIC_INPUTS entry. Build metadata discovers /llms.txt via rel=describedby without modifying visible HTML/CSS/JS or image assets. The existing server verifies that template with its manifest, snapshots its UTF-8 text and appUrl validated by the existing publicDestination function, and serves generated GET/HEAD text/plain with no-store/no ETag. Missing/unsafe app values omit that section. Exact route checks reject query and encoded aliases; no environment interpolation, file listing, external fetch, new public schema, service or dependency is introduced. The static template and manifest do not change when the app URL changes.

SITE_ORIGIN already exists as a Dockerfile ARG and build validator. Compose now forwards its optional value only under landing.build.args; the service environment remains exactly LANDING_VIDEO_URL and LANDING_APP_URL. Empty origin preserves local robots/metadata and generated-text noindex. Explicit HTTPS origin generates canonical/sitemap of landing, not app. Real domain confirmation does not establish DNS/TLS/deployment/indexing. Changing this build origin is distinct from changing the two startup destinations without rebuilding.

The approved visual composition and MP4 are byte-preserved. Reuse their R3 evidence by identity; evaluate the new text/boundary/cache/startup A→B→A/origin wiring, operator documentation and existing landing CI selection. Focused tests and real isolated HTTP replace neither future CI at the definitive commit nor human pairing/reviews. The initial R4 image build is explicitly authorized; no subsequent destination-change rebuild is needed.
