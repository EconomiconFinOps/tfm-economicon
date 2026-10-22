# Revisión y validación — JUP-089

## Candidato

Candidato histórico de R1/R2 y adendas finales del 19/10/2026: rama feat/JUP-089-public-landing; HEAD/base f444ba11e38203b6cfd645a098fd9946d55955e3 más diff de trabajo. Proceso del checkout: CONTRIBUTING.md, 2026-10-18 (JUP-126; excepción PR135 no aplicable a esta entrega). [Evidencia propia](../../../../docs/evidence/JUP-089-validation.md). Los bytes nuevos se identifican mediante sus huellas de entrega, no como contenido del commit base.

## Revisión técnica local independiente

R1: REVIEW_FAIL por P2 de integración: Turbo estricto filtraba SITE_ORIGIN/LANDING_OUT_DIR (y PORT en dev) y no diferenciaba los valores en su huella. Informe original conservado, SHA25682a00e6c06a9759e490e1241a42e29e26729cde152e2c8148b32d3b07db2a892; no se sustituye por el arreglo. Corrección R2: configuración específica de la app con entradas declaradas y caché desactivada sólo en build de landing para conservar salidas externas. Pruebas de planes efectivos y ejecuciones reales desde la raíz favorables. R2: REVIEW_PASS técnico sobre el candidato de 39 archivos sin commit; P2 R1-01 resuelto, sin nuevos bloqueantes técnicos. Informe original SHA256fd6863aef9244e366ded0c0805963f1532dce4461d2d77eef9efb52eca94e598. El Revisor ejecutó21pruebas (2Turbo y19CI), confirmó la cobertura R1 no afectada y contrastó los registros propios del liderazgo de builds/dev reales. Los controles independientes al retorno sobre las dos referencias originales R2 fueron conformes el19/10. No se atribuye aislamiento técnico a ese resultado.

## Validación funcional local independiente

R1: evidencia local favorable sin defectos funcionales demostrados; dictamen global NEEDS_CONTEXT, sin aceptación completa de la JUP. Informe original conservado SHA256c03b3ba5c275966d03343baa0367413cc86c9c21785e210897aa08f3ec37ca3e y adenda de coordinación; matriz de ocho criterios con estados explícitos. Recorridos propios1440/390/320, teclado/menú/tabs/demo/diálogos/foco y404/405, build idéntico y7/7pruebas. R2: evidencia funcional afectada favorable, sin defectos nuevos demostrados; NEEDS_CONTEXT global, sin VALIDATION_PASS completo. Informe original SHA2569055f54445d07e37f1287c7c43ede24144423015d3fb077043003175b9e28db8. El Validador ejecutó2pruebasTurbo y dev/build propios con origen/salida/puerto41792 y HTTP200/404; reconstruyó el mismo artefacto local. Confirmó expresamente la aplicabilidad de UI y evidencia R1 por18archivos de app y artefacto idénticos. Ambos roles retiraron sus recursos propios y conservan los originales R1/R2. Dominio/renovación, HTTPS/despliegue público, tiempos de pintado/CWV y preferencia reduced-motion emulada no se afirman comprobados. HTTP/tamaño y contrato CSS estático tienen los límites declarados y aceptados para continuar las evaluaciones locales por el liderazgo el19/10/2026.

## Reviews humanas, CI y publicación

Pendientes: Revision JUP-089 de Alejandro y Validacion JUP-089 de Lucía según los roles propuestos, participación real de pairing y estado remoto de CI/PR. Asignación no acredita participación. Hacia develop, primer dictamen humano favorable Comment y segundo Approve cuando ambas estén satisfechas. No hay PR publicada ni autorización de merge por esta entrega.

## Human Approval

Diseño: aprobado por Paris el19/10/2026 según comunicación del liderazgo.

Paris aprobó el cierre local y autorizó archivo, commit y push el 19/10/2026, según comunicación PM. El cambio se archivó como 2026-10-19-jup-089-public-landing y PM publicó el commit 481b4cffaf7f67607068246455834af59c14b4d8, conservando base f444ba11 y fuentes funcionales. Esta autorización no es aprobación de PR, cierre público, permiso de despliegue o merge, ni acredita reviews humanas.

## Corrección posterior de CI — 19/10/2026

PM comunicó el fallo de gobernanza del [run39268057889](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39268057889) sobre481b4cf: dos fallos de CiWorkflowTests en test_evaluation_scripts.py. Reproducción propia antes de editar:2FAIL/2PASS en la clase afectada. La lista literal CI_BLOCK_TODAY omitía node --test tools/landing-turbo.test.mjs; se añade en su posición sin cambiar workflow, aserciones, orden, unicidad o sangría. Después del arreglo:16pruebas del módulo y19del contrato CI favorables. No se repitió la suite remota de1842casos ni se modificó producto/configuración/dependencias.

Nuevo candidato: HEAD481b4cffaf7f67607068246455834af59c14b4d8 más delta local de este fix, misma rama/base estable. Los informes históricos R1/R2 no se modifican ni se extienden automáticamente: evaluación independiente afectada del fix y CI remota sobre su futura publicación PENDIENTES. La aprobación y archivo anteriores se conservan como hechos fechados; no se afirma un nuevo permiso de publicación.


## Reconciliación posterior — 22/10/2026

PR142 se reconcilia localmente desde c684210275e2788de2c660b52cf3ad8098d7fd32 con develop c00063dbaa83a1237431edef9de6d71d1bfd1ffd sin commit; único conflicto documental conserva ambas filas. Diseño, 20 fuentes de app, contratos y artefacto c684 intactos. 46 pruebas focales, builds raíz y 13 peticiones reales favorables, con registros separados. Se conservan fixes publicados y todo feedback anterior; no se cambia ni rearchiva esta especificación. Véase la [matriz vigente](../../../../docs/evidence/JUP-089-validation.md#estado-vigente-delta-local-c684--c000--22102026).

Revisión y validación independientes del candidato fijo requieren nuevas referencias originales y conservan los límites. La tarea4.4 sigue pendiente: resultados locales y pairing documentado sobre c227 no equivalen a reviews humanas afectadas, CI nueva o aceptación pública. Dominio/renovación, alojamiento/DNS/HTTPS/despliegue/reversión públicos, vídeo y destino auténtico de demo siguen pendientes; reduced-motion interactivo NOT_VALIDATED, límite aceptado y explícito. No se autoriza commit/push/publicación o merge por esta reconciliación. El liderazgo mostrará informe y borrador antes de subir nada.


Comprobaciones nativas de este corte: OpenSpec estricto **88 PASS/0 FAIL**, trazabilidad e higiene conformes (2.305 fuentes). Git diff --check PASS con Git Windows. El primer intento Git WSL no pudo resolver la ruta Windows de objetos alternativos del checkout; error de entorno conservado, sin cambiar objetos/configuración, y sólo ese control se completó con el Git del host. No es un fallo de producto o una guarda fallida. Los 104 controles de política PR y 15 de gobernanza de c684 se reutilizan por identidad comprobada de todas sus herramientas, fixtures, plantillas, proceso y entradas de gobernanza/workflows; no se presentan como ejecutados otra vez. CI remota del candidato sin commit pendiente.


## Incremento de base para publicación — 22/10/2026

R1 local sobre c684+c000 terminó con revisión y validación focales favorables; el liderazgo lo conservó como commit local c72f99f47eff36b72d6a51df4b314f3f33dab0af. Paris autoriza subir, comprobar CI y solicitar a Lucía revalidación sólo del delta. Se incorpora develop4567e8e7667c3fa5ad2d17eedd2f3da7a332e4bb/PR151 sin commit todavía de esta segunda integración; el conflicto de índice conserva ambas filas y todos los cambios entrantes. Las 20 fuentes de landing,11contratos y entradas de pruebas R1 mantienen identidad; reutilización explícita de46pruebas/builds/HTTP/UI/Lighthouse, sin baterías nuevas. Se ejecutan sólo controles documentales afectados; los mismos evaluadores emiten adendas independientes con referencias nuevas, sin sustituir originales. Véase el [incremento vigente](../../../../docs/evidence/JUP-089-validation.md#incremento-vigente-para-publicación--22102026).

Sin cambios de producto, requisitos o rearchivo. La tarea4.4 y los requisitos humanos/públicos conservan su alcance; aprobaciónLucía c227 dismissed es histórica, pairingVíctor c227 preservado y reduced-motion interactivo NOT_VALIDATED aceptado. Autorización de publicación no acredita CI del SHA futuro, aceptación pública o merge. Git/publicación a cargo del liderazgo.


Controles documentales de este incremento: OpenSpec estricto89/89, trazabilidad e higiene conformes (2.332fuentes); enlaces locales comprobados. Diff del aporte PR142 contra develop4567 conforme. La comparación con HEADc72 detecta una línea vacía final en la especificación entrante assistant-evaluation-composition: se reproduce idéntica en c000→4567 y se conserva sin modificar trabajo ajeno; no es una regresión propia ni se oculta el resultado adverso. Sólo se usaron herramientas Windows ya existentes; el runtime WSL temporal anterior no estaba disponible y no se instaló/configuró ningún reemplazo. No se repitieron pruebas de producto.
