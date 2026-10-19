# Evidencia de la landing pública — JUP-089

Verificación local: 19/10/2026. [Tarjeta](https://trello.com/c/fD7nJKRl) · [OpenSpec archivado](../../openspec/changes/archive/2026-10-19-jup-089-public-landing/). Rama feat/JUP-089-public-landing; base evaluada f444ba11e38203b6cfd645a098fd9946d55955e3 más diff de trabajo. Los archivos nuevos no se atribuyen al SHA base. Pruebas propias del liderazgo y evaluaciones independientes R1 conservadas; reevaluación R2 técnica favorable y funcional local favorable, con criterios completos públicos pendientes. Paris aprueba el cierre local y autoriza el archivado, commit y push el 19/10/2026; la aprobación no acredita despliegue público ni reviews humanas.

## Resultado local y límites

App estática independiente, sin cambios al frontend privado, autenticación o API, ni dependencias de producción nuevas. Siete secciones y recorrido aprobados. Datos, fuente, respuesta y acciones ilustrativas rotulados; no se promete Azure conectado, causa demostrada, previsión, ahorro o vídeo.

El diseño visible fue aprobado por Paris el 19/10/2026 según comunicación del liderazgo. Se conservan fuentes, logos, composición y recorrido. Correcciones ordinarias autorizadas: coral→lila/índigo en la candidata de anomalía (ADR-0012 y frontend-brand-identity), contraste de textos secundarios/foco/índice y orientación ARIA según disposición de pestañas. La aprobación estética no sustituye aceptación de publicación ni reviews humanas.

## Criterios oficiales facilitados por liderazgo el 19/10

| Criterio de la tarjeta | Evidencia/resultado | Pendiente |
| --- | --- | --- |
| Dominio y renovación | Configuración acepta origen HTTPS explícito; sin origen el artefacto es noindex | Elegir/aprobar dominio o subdominio, titular y responsable; no se ha registrado nada |
| HTTPS y ausencia de secretos/datos internos | Lista cerrada de archivos, symlinks rechazados, huellas verificadas y pruebas de rutas privadas; sólo datos ilustrativos | Certificado, HTTP→HTTPS y cabeceras en dominio público; loopback HTTP no los acredita |
| Responsive y accesibilidad básica | 1440/390/320 sin overflow; menú, tabs con teclado, diálogo/cierre/Escape/retorno de foco; 15 muestras de contraste cumplen su umbral; imágenes con alt y controles con nombre | No auditoría WCAG completa ni dispositivos físicos; preferencia reduced-motion no emulada |
| Copy respaldado y simulación visible | Composición aprobada, rótulos y límites de coste/candidata/fuentes; cuatro nombres sin cargos inventados | Destino de demo real aún no conectado |
| Rendimiento, accesibilidad y SEO medidos | 230138 bytes en 14 archivos, mediana HTTP loopback 1,41ms en 5 muestras; contraste y estructura DOM medidos; metadatos/local-noindex y origen de prueba cubiertos | Sin Lighthouse/FCP/CLS/CWV ni medición del dominio final; no equivalen a tiempos de usuario |
| Enlaces, vídeo si existe, metadatos y404 | Navegación de secciones, licencias/recursos servidos con hashes, título/description/OG/favicon/robots/sitemap y404 HTTP+visible | No hay vídeo: no se inventa; URLs definitivas dependen de origen aprobado |
| Deploy y rollback | Build reproducible, _headers generado desde política compartida y [manual de operación](../operations/public-landing.md) | Propuesta de hosting no aprobada, sin despliegue ni rollback público ejecutados |
| PR revisada, CI y evidencias | Checks locales indicados abajo, job CI adicional con permisos/acciones existentes | Aprobación final, archivo/publicación autorizados y reviews humanas/CI remota |

## Pruebas y mediciones

[Datos compactos](JUP-089/measurements.json). Windows, Node24.17.0 (contrato Node22+, CI Node22), pnpm9.0.0 y OpenSpec1.8.0. Instalación frozen-lockfile correcta; 612 paquetes reutilizados, sin dependencias nuevas de producción.

| Comando | Resultado |
| --- | --- |
| corepack pnpm jup:check:all | 10 changes enlazados, incluido JUP-089 |
| corepack pnpm pr:check:test | 104 PASS |
| corepack pnpm ci:check:test | 19 PASS, incluido job landing |
| corepack pnpm repository:governance:test | 15 PASS |
| corepack pnpm openspec:validate | 82/82 PASS |
| corepack pnpm test --filter=@finops/landing | 7 PASS, 0 omitidas |
| corepack pnpm build --filter=@finops/landing | PASS, artefacto estático |
| corepack pnpm lint --filter=@finops/landing | PASS |
| corepack pnpm jup:cleanup:check | PASS |

Las suites/build de producto se limitan a la nueva app afectada, según alcance aprobado. Se ejecutan los controles locales obligatorios aplicables y no se repiten baterías Python/RAG/frontend ajenas: no se alteran sus archivos ni dependencias; el lockfile sólo añade un importer vacío y la instalación congelada conserva resolución. Los jobs completos de CI remota siguen pendientes de publicación, no se declaran ejecutados localmente.

Riesgos focales cubiertos: archivos privados, origen inválido, symlinks, build fallido conserva salida válida, integridad de bytes, MIME/HEAD/ETag, rutas desconocidas/traversal/métodos y404 real. Primera ejecución tras añadir _headers: 6 PASS/1 FAIL por orden erróneo del array esperado; se corrigió el orden exacto sin debilitar aserciones y las siete pasan. Medición de contraste detectó índice inactivo2,86:1; corregido y repetido con15/15 muestras conformes. Se conservan los fallos originales en la evidencia de trabajo del liderazgo.

El navegador de comprobación no expone tiempos de pintado ni emulación de reduced-motion. Se midió HTTP/tamaño por separado sin presentarlo como renderizado de usuario. La regla reduced-motion tiene scroll auto y animación/transición none; está comprobada estáticamente, no como preferencia emulada. Se ha elevado este límite al liderazgo y no se marca un PASS público o de auditoría completa.

## Evaluación independiente y corrección R2

R1: revisión técnica REVIEW_FAIL por integración Turbo (P2), validación funcional con evidencia local favorable y dictamen global NEEDS_CONTEXT por criterios públicos completos pendientes. Se conservan los informes originales y su atribución en [review.md](../../openspec/changes/archive/2026-10-19-jup-089-public-landing/review.md). El control independiente al retorno fue conforme antes de corregir. No acredita aislamiento técnico ni ausencia de transitorios; se preserva el intento denegado de Turbo de crear un log, sin escritura efectiva observada.

El arreglo R2 declara SITE_ORIGIN/LANDING_OUT_DIR y PORT de dev en la configuración específica de landing. El hash cambia con origen/salida/puerto y el build desactiva su caché para no restaurar artefactos en un destino relativo distinto del externo solicitado. No cambia HTML/CSS/JS ni los bytes del artefacto local. Pruebas afectadas:28PASS (7landing,19CI,2planesTurbo). Tres builds reales desde la raíz verifican canonical con dos orígenes sintéticos distintos, ausencia del origen anterior, salidas externas y regreso a noindex con el mismo manifiesto de artefacto e9393f135b66bc8af7f6b8c6f7f988b5d31d1641d0edd9a8ccbac0ce46c0a7f0. El dev raíz respondió200 en el puerto temporal solicitado41793 con origen y salida externos correctos; servidor retirado. El primer comando de build tenía el argumento cache-dir mal formado por PowerShell; su fallo original se conserva y no es defecto de producto.

R2 independiente: REVIEW_PASS técnico; el Revisor ejecutó21pruebas afectadas (2Turbo y19CI), dio por resuelto el P2 y confirmó aplicabilidad de su revisión R1 no afectada. Validador: afectado local favorable sin nuevos defectos; ejecutó2pruebasTurbo y dev/build propios con origen/salida/puerto41792, HTTP200/404 y artefacto local idéntico, confirmando expresamente reuso de UI/evidencia R1. NEEDS_CONTEXT global se mantiene por los criterios completos pendientes. Informes y huellas conservados en review.md. Los dos controles independientes al retorno sobre las mismas referencias originales R2 fueron conformes antes de este cierre documental. No sustituyen aprobación humana, CI o comprobaciones públicas.

## Vistas reales de la implementación

![Escritorio1440](JUP-089/desktop-1440.jpg)

![Móvil390](JUP-089/mobile-390.jpg)

[Móvil320](JUP-089/mobile-320.jpg) · [404 móvil](JUP-089/404-mobile.jpg). Las dimensiones CSS de prueba pueden diferir de los píxeles codificados por scrollbar/escalado de captura. Comparación visual con la maqueta aprobada, sin afirmar identidad de píxeles ni puntuación estética objetiva.

## Participación y cierre

Roles propuestos por la tarjeta: Paris liderazgo, Víctor pairing, Alejandro revisión y Lucía validación. No se acredita participación por asignación. No se ha reutilizado HTML/CSS/JS de PR106; los binarios de marca/fuentes conservan su atribución. No existen aún las dos reviews humanas de esta entrega ni permiso de merge.
