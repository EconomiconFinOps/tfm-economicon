JUP: JUP-140
Trello: https://trello.com/c/rXLyK4g4

## Why

Los destinos de vídeo y aplicación ya están facilitados, mientras la landing sólo tiene un recorrido ilustrativo y un build estático. Paris aprobó el diseño Docker/Compose v2 el23/10/2026: configurar los destinos al arrancar y poder cambiarlos recreando únicamente landing con la misma imagen.

## What Changes

- Añadir imagen Node22 por digest y servicio landing sin perfil en Compose GENERAL, con salud local, usuario no privilegiado, raíz de sólo lectura y frontera de red propia.
- Leer LANDING_VIDEO_URL/LANDING_APP_URL al arrancar; publicar únicamente videoUrl/appUrl mediante recurso del mismo origen no cacheable, sin modificar dist ni exponer el entorno.
- Aplicar la composición clara/oscura aprobada: único acceso app en cabecera, vídeo prominente con autoplay inicial silenciado/playsinline, controles/pausa respetada y fallback manual. Las perspectivas ilustrativas permanecen separadas.
- Servir sólo la copia local aprobada desde directorio público dedicado fuera del checkout y de la imagen, bind readonly, manifiesto de MIME/tamaño/SHA y snapshot máximo50MiB. Ruta media cerrada con GET/HEAD/Range206/416 y forma relativa de vídeo restringida; no nuevo servicio/dependencia/variable pública.
- Conservar la CSP existente: media del mismo origen ya permitida por default-src self; no abrir orígenes, cookies o permisos. Visores HTTPS externos sólo como enlace secundario. No atravesar Cloudflare Access.
- Comprobar A→B→A con la misma imageID/assets y recreación sólo de landing, sin rebuild, pull, commits o PR; conservar los otros servicios.
- Actualizar operación, tests y consumidores de Compose/topología/CD afectados; documentar los criterios AC1–10 y límites reales.

## Capabilities

### New Capabilities

Ninguna: ampliar public-landing.

### Modified Capabilities

- containerized-runtime: declarar uid/gid10001 y mode0700 del tmpfs processor para el arranque general, extensión mínima aprobada por Paris el23/10/2026.
- public-landing: destinos públicos de arranque, vídeo local nativo, temas y perspectivas ilustrativas, configuración/health y media seleccionada verificada. Frontera ampliada expresamente sólo al directorio público dedicado, sin acceso arbitrario al host.

## Impact

apps/landing (Dockerfile, arranque/servidor, UI, CSP y pruebas), Compose general, ejemplos de entorno, contratos Turbo/topología/CD directamente afectados y documentación. Sin dependencias de producción adicionales, migraciones, APIs privadas o modelos. Base oficial PM 3d4e57490ab7c324023ea78e42775871134e6b0c comprobada en el checkout asignado feat/JUP-140-landing-runtime-links; HEAD contiene esa base y parte limpio. No escribir en develop ni en candidatos existentes.

## Human Approval

- Approval type: pre-code
- Decision: approved
- Approver: Paris Arcos
- Date: 2026-10-23
- Source: aprobación comunicada por PM y aprobacion-diseno-implementacion-PM-20261023.json
- Approved design SHA256: 51c3d34b2898450cb8ef28f79a2df76e2a1b69490759cf581b98b735ebfaace0
- Limits: checkout adicional autorizado y preparado por PM el 23/10/2026; implementación y recursos temporales propios autorizados, sin escrituras Git. No archivo, commit/push, PR, publicación, despliegue, merge, gasto ni Cloudflare Access.

## Approved narrow extension23/10/2026

Paris autorizó «Sí, aplicar y comprobar ese cambio mínimo»: sólo processor.tmpfs /tmp→/tmp:uid=10001,gid=10001,mode=0700 y prueba/documentación asociada. PM verificó retorno R1 contra sus mismas guardas originales antes de corregir. Sin cambiar código/Dockerfile/usuario del processor ni ampliar permisos. El fallo y los dictámenes originales R1 se conservan; la corrección requiere evidencia propia y reevaluación afectada con nuevas referencias.

## Corrección UX posterior aprobada — R3,23/10/2026

Paris revisó la demo y ordenó panel de vídeo dentro de la página, único Abrir aplicación en cabecera también en móvil, jerarquía/cierre más claros y retirada de mensajes técnicos de éxito. Fuente: encargo PM20:26:47 y revision-ux-20261023/encargo-correcciones-ux-PM.md. Se conserva marca, tipografía, colores y recorrido. La franja identifica proyecto académico; la simulación se advierte junto a las ilustraciones.

El criterio nuevo requiere reproducción REAL dentro del panel: fallback no basta. Investigar Drive mediante documentación oficial y navegador; no relajar sandbox/CSP/privacidad, ampliar permisos/orígenes ni descargar/rehostear vídeo sin decisión humana específica. Candidato R2 y2508fuentes originales se conservan externamente; sus PASS no se extienden a R3. Dos nuevas guardas PM antes de los mismos evaluadores. Se mantiene la dispensa interactiva reduce como NOT_TESTED, sin nuevos intentos o preferencias. Base3d4 estable; sin Git/publicación/gasto.

## Ampliación visual y suministro local aprobados —23/10/2026

Paris aprobó expresamente «Aprobar el diseño» y «Autorizar copia y suministro local» después de revisar la propuesta externa SHA256ea1d668b73f293167b8d7a91be220307f245a671aa90b4eb1182c17f43b6c79a. Se autoriza su composición inspirada en Chargebee con recursos/colores propios, claro/oscuro y selector accesible, vídeo prominente con autoplay silenciado, controles y pausa. El único MP4 autorizado se descarga a recurso propio y se sirve sólo localmente desde directorio público dedicado RO/manifiesto/SHA/snapshot50MiB. Si requiere conversión, más tamaño o permisos nuevos se consulta antes; no convertir ni ampliar unilateralmente.

Paris confirmó además «Confirmar construcción inicial y prueba local»: la construcción inicial de código modificado no contradice la invariancia posterior. Cambios de vídeo/enlaces mantienen misma imagen sin rebuild ni PR. También pidió preparar fuera del repositorio vídeo/manifiesto y pasos exactos para el compañero; no autoriza enviarlos, publicar imagen o desplegar externamente. La huella del medio no se mezcla con el build estático.

El visor Drive negro y R2/R3parcial/propuesta se conservan como cortes históricos. El nuevo criterio exige avance real de tiempo inline sin Play para autoplay, errores independientes, ambos temas/móvil y procedimiento de recuperación. Dos nuevas guardas originales PM antes de los mismos Revisor/Validador; no se heredan PASS previos. Se mantienen roles humanos y base3d4, dispensa interactiva reduce NOT_TESTED y prohibiciones de Git/archivo/publicación/gasto/Access.


## Approved R4 additions —23/10/2026

After approving the R3 visual result, Paris expressly required clearer application-env and video playback recipes plus a factual discoverable llms.txt before publication. He confirmed the real landing origin separately from the application destination. The narrow implementation adds an explicit verified description template and GET/HEAD generated text from the same validated startup app snapshot, rel=describedby metadata, and wires the existing SITE_ORIGIN build argument through general Compose. It does not add a runtime destination variable, service, dependency, provider call, visual redesign or external access. Empty-origin local noindex is preserved; a configured origin does not establish public accessibility or indexing.

The R3 result, original media, independent reports, prior documentary closure and external PR drafts remain historical. R4 requires its own focused evidence, fixed manifest and independent affected evaluation before presentation; previous PASS and human visual approval are not silently extended to new behavior. Archive, Git, PR publication, deployment and merge remain separately unauthorized.
