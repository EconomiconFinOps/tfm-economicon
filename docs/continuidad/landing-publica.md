# Landing pública — JUP-089

Actualización documental: 22/10/2026. Los cortes anteriores conservan sus revisiones y límites. [Tarjeta](https://trello.com/c/fD7nJKRl) · [OpenSpec archivado](../../openspec/changes/archive/2026-10-19-jup-089-public-landing/) · [Evidencia](../evidence/JUP-089-validation.md).

## Estado vigente: reconciliación local de PR142 — 22/10/2026

Paris autoriza reconciliar el HEAD publicado `c684210275e2788de2c660b52cf3ad8098d7fd32` con develop `c00063dbaa83a1237431edef9de6d71d1bfd1ffd`, comprobar el delta con revisión/validación independientes y mostrar resultados antes de subir nada. La integración se prepara sin commit; único conflicto en el índice de continuidad, resuelto conservando una vez las filas de landing y modelo único. Las operaciones Git y los controles originales de evaluación corresponden al liderazgo; esta preparación no autoriza commit/push, publicación, despliegue o merge.

Los 20 archivos de apps/landing y 11 contratos de package/lock/Turbo/CI se conservan frente a c684. La base incorpora 98 rutas entrantes de otros trabajos; producto, Compose, IA y monitoring entrantes se mantienen sin correcciones de landing. Sólo se actualizan esta continuidad/índice, la matriz y las notas del archivo existente. No se cambia diseño, marca, demo ilustrativa, copy corregido, contraste, enlaces reales o HSTS; no se abre ni archiva otro change.

Comprobaciones nuevas: 9 pruebas landing, 21 Turbo/CI y 16 del contrato de scripts, todas PASS y sin omisiones. Build/lint desde la raíz y salidas externas local/HTTPS sintético conformes. El artefacto local se compara con una reconstrucción independiente desde las fuentes c684 exportadas: 14 entradas públicas, 231.052 bytes y manifiesto SHA256 `8a475d9747d6161c3fbe1e2b673f075ef26e916e86ece7404dfaf1932442a502`, idénticos en ambas. La portada mantiene SHA256 `65bd5a69ef4896099891c0f06e1ee3d24a194b6ecaec71746f6ad55cc432edbf`. No son las cifras del artefacto anterior c227; no se reescriben sus registros.

Trece peticiones reales al artefacto construido desde raíz acreditan home/HEAD, desconocidas y privadas, traversal, URI inválida, método no admitido, robots y ETag; preview efímera propia cerrada, sin listener. HTTPS configurado en metadatos no significa HTTPS público. Se reutilizan la evidencia visual c684 1440/390/320 y Lighthouse local desktop100/100/92 y móvil97/100/92 por identidad de fuentes/artefacto, conservando fecha, alcance y limitaciones. No son auditorías nuevas ni se repiten baterías IA/RAG, UI completa o campañas.

Roles vigentes: Paris liderazgo, Víctor pairing, Alejandro revisión, Lucía validación. Se conserva el pairing documentado por Víctor sobre c227 como contraste posterior y pruebas, sin coautoría de construcción ni atribución de estas nuevas correcciones. Las tres reviews de Lucía sobre c227, incluida la aprobación luego dismissed por push, y el comentario de c684 se mantienen como historial; no existen cambios solicitados activos en el contexto suministrado. CI PR8/8 y SQL correctas de c684 no acreditan esta nueva composición. La descripción remota todavía conserva c227 y requiere actualización autorizada posterior.

Lectura/revalidación humana afectada y resultados independientes nuevos conservan sus requisitos. Dominio/renovación, hosting/DNS/HTTPS y despliegue/reversión públicos, vídeo aprobado y destino auténtico de demo siguen pendientes. Reduced-motion interactivo **NOT_VALIDATED**, límite aceptado y preservado; el CSS estático y la evidencia normal no lo convierten en PASS. La evaluación local no cierra la historia ni acredita aceptación pública. La matriz enlazada separa resultados nuevos, reutilizados y pendientes. Las secciones siguientes son históricas.

## Alcance y decisiones

apps/landing es una aplicación estática independiente. Conserva la composición de siete secciones y demo ilustrativa aprobadas por Paris el19/10/2026. No cambia el frontend privado, autenticación o API. Se han corregido contraste/foco y color de anomalía conforme a ADR-0012, sin rediseñar. Recursos originales/licenciados, sin código HTML/JS recuperado de PR106.

## Resultado técnico local

La evaluación local original se realizó sobre f444ba11 más diff de trabajo en feat/JUP-089-public-landing. Tras aprobación de Paris, PM archivó el cambio y publicó481b4cffaf7f67607068246455834af59c14b4d8 el19/10, con fuentes funcionales idénticas y basef444 estable. Build de lista pública cerrada, manifiesto/huellas, symlinks rechazados, preview loopback con404 real y cabeceras. Sin SITE_ORIGIN se genera noindex; el origen HTTPS explícito habilita canonical/OG/sitemap coherentes. [Uso](../../apps/landing/README.md) y [operación/reversión](../operations/public-landing.md).

Pruebas focales7/7, OpenSpec82/82 y controles nativos aplicables favorables. Navegador1440/390/320, teclado/menú/demo y15muestras de contraste comprobados; medidas HTTP locales y tamaño en evidencia. Sin emulación reduced-motion ni tiempos de pintado/CWV: límites explícitos, no aceptación pública.

## Evaluación y corrección

R1 conservada: REVIEW_FAIL técnico por variables/caché de Turbo; validación local favorable sin defectos funcionales, NEEDS_CONTEXT global por criterios públicos pendientes. Tras control independiente de retorno conforme se corrigió la integración mediante configuración exclusiva de landing. R2:28pruebas afectadas PASS, tres builds raíz/orígenes/salidas externas y dev en puerto solicitado correctos; artefacto local idéntico. No hay delta de UI. R2: REVIEW_PASS técnico (21pruebas propias del Revisor) y validación funcional afectada favorable (2Turbo y dev/build propios), con aplicabilidad R1 confirmada por cada rol. NEEDS_CONTEXT global permanece. Ambos controles de integridad originales R2 conformes y recursos de evaluadores retirados; originales conservados.

## Corrección posterior de CI

El run39268057889 de481b4cf detectó dos fallos del contrato esperado de gobernanza: faltaba la línea de regresión Turbo en CI_BLOCK_TODAY. Reproducción focal2FAIL/2PASS antes de editar; corregida la lista exacta sin alterar aserciones/workflow/producto. Módulo afectado16PASS y contratoCI19PASS. Evidencia adversa conservada; nuevo delta local sobre481b4cf con evaluación independiente y nueva CI remota pendientes. No se repitieron1842casos ni UI/entornos ajenos.

## Pendientes

Archivo y commit/push previos ya autorizados y ejecutados. Pendientes: evaluación independiente del fixCI, commit/push del arreglo por PM y nueva CI remota; autorización de PR/publicación y reviews humanas. Dominio/renovación, hosting/HTTPS público y destino de demo real no están decididos; no se cierra la JUP con localhost. Direct Upload de Pages se documenta sólo como propuesta y no permite convertir el mismo proyecto a Git integration. No se ha desplegado, comprado ni modificado DNS.

## Reconciliación con develop — 20/10/2026

Paris autoriza reconciliar PR142 conservando su estado de borrador. El candidato
parte de a5a3e9f1c87a89142c8f7dc52883a126f5cc55d6 e incorpora
88a6ce4c8a6c523c061e82a0a1f63f495f5db8ec. La preparación local anterior al
commit final no se atribuye a un SHA nuevo todavía inexistente. El único conflicto
es el índice de continuidad: se conservan la fila de landing y la del panel JUP-065.
Se actualizan únicamente este tema, su fila y la evidencia de JUP-089.

Los20 archivos de apps/landing permanecen idénticos a a5a3e9f1, así como sus
contratos de Turbo/CI y dependencias. Los2177 archivos de develop ajenos a la
aportación original permanecen byte a byte iguales. La instalación frozen-lockfile
es correcta. Pasan163 pruebas focales/nativas (104política PR,19CI,15gobernanza,
7landing,2Turbo y16contrato de scripts CI), OpenSpec83/83 y las9trazas activas.
Dos builds desde la raíz respetan el destino externo y el origen HTTPS sintético;
el manifiesto local conserva SHA256e9393f135b66bc8af7f6b8c6f7f988b5d31d1641d0edd9a8ccbac0ce46c0a7f0.
HTTP local200/404, HEAD, cabeceras y ruta privada404 comprobados; servidor propio
retirado. No se repiten UI completa ni suites de chat/RAG ajenas a la landing.

Estos datos actualizan los pendientes históricos del fixCI: según comprobación
PM del20/10, a5a3e9f1 ya está publicado en PR142Draft y su CI/SQL son correctas.
Los dictámenes de esta composición y la CI del commit resultante deben identificar
el candidato final; la evidencia antigua conserva su fecha y cobertura. La
revisión y validación independientes afectadas preceden al commit/push del PM.

El alcance público completo sigue pendiente: dominio/titular/renovación,
alojamiento, HTTPS, despliegue/reversión y destino auténtico de demo. Tampoco se
acreditan pairing de Víctor o reviews humanas de Alejandro/Lucía por asignación
o por informes de agentes. Sin publicación web, DNS, gasto, nuevos accesos,
cambios de roles, Trello o merge. Las previews previas41789/41790 se conservan.

## Reconciliación y reviews — 21/10/2026

Se prepara merge local sin commit de c22713a2 con develop bc94a4da; conflicto
del índice resuelto conservando ambas filas. Los cambios entrantes ajenos quedan
intactos. Se añaden enlaces auténticos a repositorio/docs, pie sin identificador
interno, distinción integrado/simulado/pendiente y dos pruebas de build/HSTS.
La marca y composición aprobadas se conservan. Dos textos secundarios recuperan
contraste al retirar opacidad, sin cambiar la paleta.

9/9 pruebas landing y140controles Node favorables; build raíz/lint correctos,
OpenSpec88/88,10trazas activas e higiene conformes. Lighthouse local:
escritorio100/100/92, móvil97/100/92 (rendimiento/a11y/SEO). Consulta de robots
del auditor bloqueada por CSP; HTTP directo correcto, sin debilitar políticas.
Responsive/teclado/diálogo comprobados y reversión local de artefacto por SHA256.
[Evidencia actual y límites](../evidence/JUP-089-validation.md#reconciliación-y-observaciones-de-las-reviews--21102026).

Este corte prepara el candidato para referencias de integridad y evaluación
independiente nuevas; no atribuye CI ni dictámenes anteriores al delta.
Dominio/renovación, hosting/HTTPS público, vídeo aprobado y destino real de demo
son decisiones externas pendientes. Las tres reviews suministradas se conservan:
la aprobación de Lucía era local sobre c227 y no sustituye revisión de Alejandro,
pairing de Víctor ni revalidación afectada posterior. Sin commit/push/despliegue.
