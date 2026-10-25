# JUP-140 — evidencia local de vídeo, destinos de arranque y Compose

## Hito vigente — R4 aprobado, 24/10/2026

Paris aprobó el resultado R4 después de dos evaluaciones locales favorables y controles originales conformes. Autorizó archivo OpenSpec y reconciliación con develop, con evaluación independiente afectada y presentación del cierre antes de publicar. [R4](JUP-140-R4.md) · [Cierre de archivo](JUP-140-closure.md). La base actual es 93624f77; el mapa de normalización separa conversión CRLF→LF de identidad RAW. Los cortes siguientes conservan su fecha y límites; no se reescribe ningún dictamen original. Sin autorización de publicación, merge o despliegue.

## Ampliación vigente R4 —23/10/2026

Después de aprobar R3, Paris pidió descripción llms.txt e instrucciones app/vídeo y confirmó el origen real de landing. [Resultado R4, HTTP y límites](JUP-140-R4.md) · [Operación](../landing-runtime.md). Implementación/pruebas propias preparadas; evaluación independiente afectada y cierre R4 aún pendientes. La aprobación y resultados R3 siguientes conservan su alcance, no se extienden automáticamente al nuevo comportamiento.

## Cierre local R3 aprobado —23/10/2026

Revisión técnica y validación funcional locales independientes favorables, comprobaciones finales y revisión visual completa. Paris aprobó expresamente el resultado y pidió preparar la PR para ver su título y descripción antes de publicar: AC10 local cumplido. [Resultado actual, capturas y criterios](JUP-140-R3.md) · [Operación y traspaso](../landing-runtime.md).

El cierre posterior sólo documenta el resultado y añade capturas; conserva implementación, medio y cortes R1/R2/parcial/propuesta/R3. El movimiento reducido interactivo sigue NOT_TESTED por dispensa, los SKIP/fallos históricos no se convierten en PASS y las reviews/pairing humanos aún no se acreditan. Archivo, Git, publicación y despliegue mantienen permisos separados. Los apartados siguientes conservan su fecha, incluido el estado anterior a evaluación.

## Corte R3 anterior a evaluación independiente — histórico

Paris aprobó diseño claro/oscuro, suministro local50MiB y construcción inicial/prueba propia. El vídeo verificado (21094149bytes/videoMP4/SHA7e9bdfb148cee61acb2e96837f041a5014f3f7048bf2a244a5cb20128f080292,H264/AAC18,900998s) queda fuera de Git, imagen y build, en directorio público dedicado RO. Snapshot verificado y ruta media cerrada, esquema runtime de sólo dos campos, sin nuevos orígenes o dependencias.

| Criterio y ampliación humana | Evidencia nueva de implementación R3 |
| --- | --- |
| AC1 vídeo | Autoplay real sinPlay:0,107166→7,980490s escritorio y0,088351→8,075194s móvil, mutedtrue/pausedfalse/readyState4/playsInline. Pausa3,751781s se conserva al cambiar tema; audio cambia sólo por control explícito. No es aceptación por póster/atributos/fallback. |
| AC2 acceso app | Único href en cabecera válido, también móvil; no se navega Access ni se afirma acceso efectivo. |
| AC3 configuración | Exactamente LANDING_VIDEO_URL/LANDING_APP_URL; forma media relativa restringida, HTTPS validado para enlace. No destinos operativos en assets. |
| AC4 invariancia | A→B→A con3containerID y un mismoimageID/manifiestoRAW/13recursos HTTP, no-build/no-pull; sólo landing propia recreada. Los otros12servicios R2 ya estaban retirados y no se afirman activos en este ensayo. |
| AC5 errores |23focalesLinux/0SKIP: URLs/schema/serialización/cache/medios/symlinks/rangos/snapshot; UI real de medio inexistente, vídeo inválido y app ausente, manteniendo otro destino. Play() rechazado probado con doble controlado; política real de bloqueo no reproducida. |
| AC6 frontera | Mismo origen bajo CSP existente; RO/manifiesto/MIME/SHA/50MiB/snapshot seleccionado; GET/HEAD/206/416, sin manifests/listados/medios no seleccionados/traversal. Medio ausente de imagen/build. |
| AC7 UX y temas |320/390/escritorio claro/oscuro sin overflow observado, menú/Escape/foco, pestañas End/flechas/Home y movimiento con pausa real. Reduce interactivo NOT_TESTED por decisión humana; CSS conservado. |
| AC8 Compose | Bind público dedicado en ComposeGENERAL, imagenNode22/no-root/readonly/no-new-privileges y salud propia. Processor.tmpfsR2 intacto.43topología+TurboPASS; arranqueGENERAL13R2 conserva fecha, no se repite pila ajena por cambiar sólo landing. |
| AC9 evaluación | Lint/build estático correctos y pruebas afectadas. Candidato fijo para dos guardas nuevas PM y Revisor/Validador distintos, sin heredar PASS R2. Globales R2 históricos se reutilizan sólo por entradas no afectadas y juicio independiente. |
| AC10 presentación | Diseño aprobado; implementación/traspaso y resultados finales deben mostrarse después de cotejo PM. Imagen sólo local y sin distribución/publicación externa autorizada. |

Los originales y rechazos de aprobación automática se preservan fuera del producto: descarga inicialmente rechazada y luego confirmada directamente; construcción inicial inicialmente rechazada por ambigüedad «sin reconstruir», aclarada expresamente por Paris y ejecutada. Un intento de materialización de red falló antes de crear el archivo; descarga única materializada por canal aprobado. Primer build estático falló por salida de ensayo que no acababa en dist; corregido el destino, sin cambios de código/aserciones. Windows19PASS/1SKIP previo conserva su resultado; Linux final23PASS/0SKIP cubre ese caso. CUA no expone getVideoPlaybackQuality; se usan tiempos reales, no esa API, como prueba.

Comprobaciones documentales finales: OpenSpec93/93,13trazas e higiene2511 correctos;19contratos CI afectados adicionales PASS. El primer OpenSpec92PASS/1FAIL omitía los títulos de escenario Demo journey/Tabs by keyboard exigidos por el validador de reemplazo; se conservaron esos títulos con el comportamiento actual aprobado, sin restaurar el diálogo retirado. Fallo y diagnóstico originales conservados.

Los cortes siguientes son históricos; no representan una espera vigente de aprobación del diseño/suministro, ni trasladan sus dictámenes a R3.

## Histórico — propuesta externa antes de decisión

Los dos originales R2 son favorables en su alcance y PM verificó retorno contra
las mismas guardas; AC10/decisión humana siguen pendientes. El detalle R2 siguiente
se conserva como corte histórico anterior a esos dictámenes, no como espera actual.

Después de R2 se preparó una corrección UX parcial con13 tests focales PASS,
sin acreditar vídeo inline ni evaluar R3. Paris pidió luego una composición
inspirada en Chargebee y modo oscuro: se entrega propuesta externa con capturas
en ambos temas y1440/390/320. Un único enlace de aplicación y ausencia de overflow
observados en seis vistas; movimiento y pausa comprobados.66 muestras de contraste
de texto seleccionado >=4,5:1 (mínimo5,174:1), sin certificación integral WCAG.

La nueva composición no se ha aplicado al producto. Su vídeo no tiene fuente,
tiempo0 y readyState0; inline/autoplay NO probados. La limitación de Drive se eleva
con plan de suministro de mismo origen sujeto a aprobación, sin descargar medio,
añadir montajes/orígenes o relajar CSP/sandbox. No se repiten pruebas globales ni
se hace evaluación formal de una propuesta visual. Tras decisión humana:
implementación afectada, nuevas evidencias, freeze, dos guardas originales PM y
reevaluación independiente. Sin Git writes, archivo o publicación.

## Corte R2 — corrección autorizada y evidencia afectada

Paris autorizó el23/10/2026 el cambio mínimo processor.tmpfs; se aplicó después de ambos originales R1 y del cotejo PM contra sus MISMAS referencias. R1 permanece íntegro: Revisor NEEDS_CONTEXT, Validador VALIDATION_FAIL por AC8 con carencias AC7/9/10. No se convierte ese corte en PASS ni se sustituye su evidencia.

R2 cambia sólo Compose/tmpfs, su contrato de topología/OpenSpec y documentación. Código/Dockerfile/usuario del processor e inputs de todos los paquetes permanecen idénticos a R1 (842 archivos cotejados). La imagen de landing tampoco cambia. La evidencia no afectada puede ratificarse por identidad, con juicio independiente de cada evaluador.

| Punto | Resultado actual R2 |
| --- | --- |
| AC1–6 | Reutilizar únicamente la cobertura R1 que ratifique el evaluador. AC1 pasó por fallback literal al original; iframe/anónimo/captions NO acreditados. |
| AC7 | Móvil/teclado/foco/cierre y CSS conservados; interacción con reduce activo NOT_TESTED por decisión humana explícita. IAB y Chrome ya conectado no ofrecen emulación media documentada. Paris indicó «olvidate de eso es un TFM» el23/10/2026: dispensa sólo ese ensayo interactivo. CSSOM conservado comprobado; la interacción no se marca PASS ni se extiende la dispensa a otros criterios, pruebas o publicación. No se cambió ninguna preferencia. |
| AC8 | PASS de implementación: arranque GENERAL de los13 servicios propios recreados sin suplemento tmpfs y sin rebuild. Usuario y tmpfs uid/gid10001,mode0700,W_OK true,gettempdir /tmp,read_only/no-new-privileges y salud medidos. Pendiente de reevaluación independiente R2. |
| AC9 | Topología41/41 PASS, cambio OpenSpec válido. Global build canónico5/5 PASS sin caché. Global test predeterminado FAIL conservado: backend2730PASS/369SKIP/2FAIL por plazo de observación de hijos; Azure81PASS y landing12PASS, otros paquetes interrumpidos. Las2 fallidas pasan aisladas en2.09s sin cambiar código/plazos/aserciones; no prueba causa de carga. Repetición secuencial en montaje Windows CANCELLED_INCOMPLETE, con log conservado. El script canónico completo corepack pnpm test pasa después en volumen Linux propio:5/5 tareas,0 caché,7m0.655s; backend2732PASS/369SKIP, processor2674PASS/150SKIP, frontend1427PASS, Azure81PASS, landing12PASS (total6926PASS/519SKIP). No se cambian tests, aserciones o plazos; el resultado posterior no borra los2FAIL previos ni demuestra por sí solo su causa. Tres consumidores Python de Compose R2:74/74PASS adicionales, junto a topología41/41. |
| AC10 | Presentación y decisión final humanas y dictámenes R2 pendientes; no publicación. |

A→B→A R2 observa3 containerID de landing, una misma imagen,13 hashes RAW de recursos HTTP y manifiesto RAW idénticos; otros12 contenedores conservan ID/StartedAt/estado/restarts. El control negativo restart conserva las variables anteriores. Fuente relevante de landing/Compose cotejada antes/después sin cambios. Configuración temporal extra sólo de subredes libres: el tmpfs procede de docker-compose.yml del producto.

El SHA RAW del manifiesto es a863facbc16e01da4a59b5d33bd620a04894c2aad4c7454d9e7ef990f317338a. Se conserva aparte la huella semántica calculada con JSON ordenado. En R1 el campo manifest_sha256 era SEMÁNTICO, de nombre ambiguo; no acreditó un hash RAW por etapa. Se preservan campaña/helper/informes originales y la aclaración, sin afirmar discrepancia de fuente por comparar magnitudes diferentes.

Los comandos globales se ejecutan en copia externa de las2507 fuentes R1, cotejada sin discrepancias, sin .git, sin red externa ni credenciales, con Node22/Python3.12 y dependencias de desarrollo declaradas. Primera ejecución sobre montaje Windows; ejecución final sobre volumen Linux temporal propio con los mismos2507 archivos RAW cotejados antes/después,0 discrepancias, misma imagen sha256:7b2134f5b597c792389856af49b8ef48729f542ad8bdf446cabbf3599a264cf1 y límites4CPU/6GiB, red externa deshabilitada. La preparación inicial de volumen con usuario incorrecto y un cotejo prematuro mientras copiaba se conservan como fallos de preparación, no defectos de producto. Outputs sólo en entornos externos propios. Build y paquetes de aplicación siguen siendo pertinentes a R2 porque sus842 inputs permanecen idénticos; Compose/test de topología/OpenSpec se comprueban por su delta propio. Además se identifican tres suites de processor que leen Compose; sus74 casos se repiten con el archivo R2 exacto montado en sólo lectura. La referencia R1 del volumen no se modifica. Los fallos de preparación del entorno (montaje de salida/pnpm) se conservan separados de los resultados de tests. No se afirma que filtrados satisfagan una obligación global.

La revisión/validación afectadas requieren candidato R2 fijo y DOS nuevas guardas originales PM. La UI de ensayo estable es local, no una publicación. Recursos propios pendientes de retirada al terminar evaluación y demostración; no limpiar recursos compartidos.

## Histórico R1 — contenido conservado del primer corte

Los apartados siguientes describen exclusivamente R1 ANTES de la corrección autorizada y de los comandos globales. Sus pendientes y verbos de futuro no representan el estado R2 anterior.

Fecha23/10/2026. [Tarjeta](https://trello.com/c/rXLyK4g4) · [OpenSpec](../../openspec/changes/archive/2026-10-24-jup-140-landing-video-app-runtime/) · [operación](../landing-runtime.md). Base local3d4e57490ab7c324023ea78e42775871134e6b0c. Documento de implementación; no sustituye dictámenes independientes, CI del futuro commit ni aprobación humana.

## Resultado y límites

Implementación local y cambio A→B→A sobre la misma imagen comprobados. El arranque original del Compose general NO está acreditado: processor falla al buscar directorio temporal escribible. El ensayo completo funciona con un ajuste temporal propio de tmpfs del processor; propuesta de arreglo mínima pendiente de decisión humana y no incorporada al producto. No trasladar ese resultado al Compose original.

Drive original reproduce con controles y avance0:06/0:19 en la sesión disponible. El visor insertado muestra miniatura, pero al intentar reproducir queda negro; no se declara reproducción integrada PASS. El enlace alternativo siempre visible abre el original correcto. El navegador tiene sesión autenticada: reproducción anónima no validada. Subtítulos/transcripción aparecen deshabilitados en el original observado; no se prometen ni se cambia el vídeo. Sandbox/CSP se mantienen. Un ensayo acotado de delegación autoplay no resolvió el visor y se retiró.

## Criterios oficiales

| Criterio | Evidencia observada | Estado en este corte |
| --- | --- | --- |
| AC1 | Diálogo bajo clic, título/controles del proveedor y fallback exacto al original; éste reproduce con avance de tiempo. Iframe negro; sesión autenticada. | Fallback comprobado; reproducción integrada/anónima NO acreditadas. Validador debe juzgar criterio literal. |
| AC2 | Los dos href de aplicación coinciden con la configuración. Acciones de vídeo/app/recorrido separadas; texto advierte autorización propia. | Href y etiquetas comprobados; acceso efectivo NO probado ni frontera Cloudflare visitada. |
| AC3 | URLs sólo desde snapshot de arranque, esquema de dos campos, sin destinos operativos en HTML/JS de imagen; prueba A/B/A y mismos assets. | Comprobado localmente. |
| AC4 | Tres containerID distintos A/B/A, misma imageID y huellas de manifiesto/13 archivos públicos servidos. Otros doce contenedores conservan ID/StartedAt/estado/restarts. Restart tras editar entorno conserva A. | PASS local con la condición de infraestructura indicada para el resto de la pila. |
| AC5 | Tests de URLs peligrosas/credenciales/locales/IP/longitud, esquema/escape/secret sentinel, GET/HEAD/POST, no-store sin ETag/304, frontera y artefacto inalterado. Navegador: vídeo inválido deja app correcta; app ausente elimina href y conserva vídeo/recorrido. | PASS local. |
| AC6 | CSP sólo añade frame-src Drive; script-src self/connect-src none/anti-frame/nosniff/no-referrer preservados. Cero iframes antes del clic; sin preconnect/prefetch/thumbnail remoto en fuentes. Cierre retira iframe. | Cabeceras/DOM/fuentes comprobados. No hubo monitor de red completo disponible; no convertir inspección DOM en captura de tráfico. |
| AC7 | Vistas1440/390/320: scrollWidth=clientWidth1425/375/305. Menú/Escape, flechas y End con foco/panel coherentes, tres perspectivas, cierre/retorno de foco e iframe retirado. Regla reduced-motion presente en CSSOM y conservada. | Comprobado con límite: no nueva emulación interactiva de prefers-reduced-motion (preferencia disponible=false). |
| AC8 | Imagen Node22 por digest y servicio sin perfil en Compose general, red propia, usuario node, read_only/init/no-new-privileges/health local. Pila completa sana sólo después de ajuste temporal processor; docs de recreación/reversión. | CONDICIONADO: arranque original FAIL conservado y propuesta de tmpfs pendiente. |
| AC9 | Pruebas focales y Docker/navegador realizados; candidato aún pendiente de congelar con controles originales para evaluación distinta. | Evaluaciones independientes PENDIENTES. |
| AC10 | Capturas/resultados/pendientes preparados para liderazgo antes de publicar. | Presentación final/decisión humana PENDIENTES; no hay publicación autorizada. |

## Pruebas ejecutadas

- `node --test apps/landing/tests/*.test.mjs tools/docker-topology.test.mjs tools/landing-turbo.test.mjs tools/local-doctor.test.mjs tools/local-smoke.test.mjs`:134/134 PASS. La primera ejecución detectó la expectativa de puerto del doctor sin landing (130/131); corregida sin debilitar controles. Topología final40/40 tras reforzar exclusividad de red.
- Landing desde workspace: lint, build raíz filtrado a @finops/landing y12/12 tests PASS. La misma suite12/12 PASS en Node22/Linux de la imagen, con fuente de sólo lectura, tmpfs propio y sin red externa.
- Gobernanza final (`pr-policy`, `ci-workflow`, `repository-governance`, `cd-workflow`):141/141 PASS. Higiene:2507 archivos sin agentes personales, binarios ajenos ni tareas paralelas. `jup-check --all`:13 cambios enlazados. OpenSpec estricto93/93 PASS. Se conservó el escenario histórico Demo journey antes de código tras un primer rechazo de validación del delta.
- CD local con Python3.12:63 casos,60 PASS/3 SKIP; la integración real Compose omitida por opt-in se ejecutó después y pasó junto a los23 casos restantes de test_deploy (24/24). Quedan dos SKIP por modos POSIX/lock Linux no disponibles en el host Windows. Una ejecución inicial con Python3.10 falló por incompatibilidad de tarfile.filter; se conserva y no se atribuye al producto.
- Compose2.34.0, motor28.0.4 Linux/amd64 en Docker Desktop4.40.0. Proyecto/puertos/subredes propios y datos desechables; proveedores mock, CHAT/RAG OFF. Sin llamadas a modelos, nuevos accesos, gasto o uso de servicios compartidos.

Los checks se limitan a landing y consumidores afectados, además de las obligaciones de gobernanza. No se presenta una batería completa de backend/processor/frontend ni CI remota como ejecutada en este candidato. Las fuentes de esas apps permanecen intactas.

## Infraestructura e integridad

La prueba A→B→A identifica cada contenedor, imagen, manifiesto y archivo servido. La configuración B usa destinos públicos sintéticos sólo para observar href/configuración, sin visitarlos. No se reconstruye ni se descarga imagen durante el cambio. Los logs originales y los fallos de precondición se conservan en el paquete externo de evidencias; no se sustituyen por resultados posteriores.

El fallo original del processor se localizó en tempfile durante carga local de tiktoken. Su Settings valida; mismo imageID funciona con tmpfs uid/gid10001/mode0700. Esos valores posteriores sí fueron medidos. NO se midió uid/mode del tmpfs original antes de recrearlo: la propiedad original concreta sigue siendo hipótesis, no hecho. No hay parche a processor en este corte.

La infraestructura temporal propia debe retirarse al terminar evaluación y demostración, comprobando antes identidad del proyecto. La retirada y el cotejo final se incorporarán al paquete de entrega. No detener ni limpiar recursos compartidos.

## Evidencias de navegador y permisos

El paquete externo conserva capturas landing-final-1440/390/320, configuración de vídeo inválido y app ausente, diálogo del vídeo y original reproduciendo; JSON de dimensiones, campaña A/B/A y logs de pruebas. El manifiesto de entrega identifica sus bytes. No se copian credenciales de ensayo, controles personales o estado de agentes al producto.

Roles oficiales: Paris liderazgo, Alejandro pairing, Lucía revisión, Víctor validación. Su asignación no demuestra participación realizada. El trabajo local asistido no sustituye reviews humanas. No hay permiso de archivo, commit/push, PR, despliegue público, AWS/DNS o merge en este corte. OpenSpec permanece activo. Dominio/renovación, HTTPS público, acceso real a app y aceptación integral conservan sus etapas.
