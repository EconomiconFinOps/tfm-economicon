# JUP-063: evidencia de la memoria de IA

Corte: 2026-10-19. Base técnica: `f444ba11e38203b6cfd645a098fd9946d55955e3`.
[Tarjeta JUP-063](https://trello.com/c/sRKGpYEy). Estado comunicado por coordinación:
En revisión. Este documento prepara el incremento documental; no declara cierre.

## Alcance y fuente

Los apartados e (solución de IA) y g (modelos de aprendizaje automático) de
Memoria_Economicon permanecen en el documento colaborativo descrito en
[la gobernanza](../memoria/README.md). Su ubicación se obtiene de la tarjeta.
La incorporación del texto fue aprobada el 19/10 y comprobada por coordinación
contra la misma revisión canónica. No se incorporan aquí texto ni exportaciones.

La aportación aprobada contiene 28 párrafos identificados E01-E18 y G01-G10,
nueve encabezados de segundo nivel, dos tablas (63 celdas), un diagrama y cinco
enlaces técnicos fijados a la base. Grafana aparece una vez. Se distinguen
implementación, configuración, medición y aceptación humana.

El antecedente PR #95 está cerrado sin integrar. La PR #141 conserva
[la comparación histórica del 16/10](JUP-063-model-selection.md): se incorpora
allí esta aportación e/g sin reescribir sus resultados ni trasladar sus
aprobaciones a este incremento.

### Composición autorizada en PR #141

Paris autorizó expresamente el 19/10: «Autorizo la excepción para que subamos
nuestro commit a la #141, manteniendo la revisión y validación independientes.
No abras otra PR.» Sustituye la estrategia anterior de abrir una PR nueva.
Se conserva la implementación histórica de Alejandro y su autoría Iber1to;
Paris aporta la documentación de e/g. La composición local reúne
`bf7a58fdb212490b8416f3a6ba8bb501160a95cf` y
`02d96e0d47a39dd92afec8d2442f28046eb6495d`, ambos sobre la base indicada.
La excepción autoriza aportar el commit, no aprobar la aportación propia,
levantar revisiones previas ni hacer merge. Los dictámenes de e/g no se
extienden a todo #141; la composición requiere el control independiente afectado.

## Versión revisable fuera de Git

Custodia externa: `materiales/06-entregables/JUP-063-2026-10-19-eg/`.
Fecha del extracto: 2026-10-19. El manifiesto identifica la URL, pestaña y revisión
canónica, método, tamaños y hashes. Los artefactos son inmutables.

| Artefacto | SHA-256 |
| --- | --- |
| `manifiesto-2026-10-19.json` | `a46fa20362e0b155fac9fcd24631b07642cf749aa8abcd0a6b6a013f18be1e0c` |
| `Memoria_Economicon-e-g-2026-10-19.md` | `51dee6adc5fe56571703c8a2c06d1e64bc0752564b8bf4e55a7eec0abff6274b` |
| `Memoria_Economicon-e-g-2026-10-19.pdf` | `6024b39c987cb197bfd9a74d2d5a5b2502ee45c125e8f4ef10b451dec7706fd8` |
| `lectura-canonica-verificada.json` | `7e2d73bfb8847c7e7a3504dfa489fce61758fe10f9bfc66f48a32ddb453cbe50` |
| `recorrido-ia.png` | `686015eb9257f83fd4eaaa6c27ee68fb23b1ca6ad418d8fa472a33b58fac9df9` |

El Markdown procede de la lectura canónica verificada; el PDF es una reproducción
local del borrador aprobado contrastada con esa lectura, **no una exportación
nativa de Google Docs**. Tiene cinco páginas (tres de e y dos de g) y conserva
su marca de borrador. Esto no acredita el máximo de 20 páginas del documento
completo ni su aceptación humana final.

### Paginación nativa y presentación comprobadas por coordinación

El 19/10, por orden de Paris, coordinación leyó la memoria completa y comprobó
un PDF nativo de **18 páginas**, incluidas portada, índice y fuentes. SHA-256:
`a359b74a855a13e9ac8dc7b0dc42444a7fda6a6411cb0d81fe06a86ae25f15b4`.
La revisión del documento sigue siendo la de la incorporación aprobada. El
límite de 20 páginas se cumple en esta versión, **no se acredita su extensión
definitiva**: c/h siguen pendientes e i está parcialmente redactado. El índice
global requiere actualización final.

Recibos externos de coordinación: `lectura-completa-20261019/lectura-nativa-resumen.md`
(SHA-256 `6cb14141de24f456f6849f9ef77284d2370ce959abac825a01ff821ed42a029c`)
y `paginacion.json`
(`966938cd58928c50363669934412d0a1b0d0a5da08b8b63f718960d101e49a3c`).
Según esa lectura, e ocupa páginas 9-12 y g 14-16, compartidas con apartados
contiguos; las cinco páginas del extracto local no son la distribución nativa.
Este incremento registra el recibo, no vuelve a leer ni modifica otros apartados.

La presentación de Grafana local también fue comprobada por coordinación,
según `grafana-comprobacion-visual.md`, SHA-256
`6b630b0885a460b108b2d9ae39c72566dd072e8d90604b94df707e058b5c4ef4`:
cohortes, resultados, costes, latencias, reintentos y valores no medidos visibles
y diferenciados. No queda pendiente esa comprobación visual. No acredita
nuevas inferencias, otra evaluación semántica ni cambia los cortes históricos.

## Cobertura del encargo y del guion

Se ha leído la referencia íntegra del guion oficial suministrada por coordinación
el 19/10: `Guion_PJ-lectura-2026-10-19.md`, SHA-256
`ff5624edd87bff65139b59ecf57bd3dfca2851bbe36dee7499387b47471d4aaf`.
Es texto recuperado normalizado a LF, no descarga binaria, conservado fuera de
Git. Sus tres partes confirman la matriz del borrador aprobado:

| Parte del guion | Cobertura de e/g |
| --- | --- |
| Lista de entregables: solución de IA y modelos | E01-E18 y G01-G10; flujo, fuentes, decisiones y límites. |
| Requisitos técnicos: IA generativa, API, vectores y MVP funcional | E01-E02, E07-E13, E15; G01, G03-G06 y G07-G10. |
| Requisitos técnicos: monitorización, registros y rendimiento | E06-E10, E17-E18; G06 y G09-G10. La integración DevOps completa corresponde a f. |
| Requisitos funcionales: componentes, flujo y justificación | Diagrama; E03-E13 y G01-G05. Impacto y viabilidad sólo en su relación con IA, E01-E02, G01, G04 y G08; el caso de negocio pertenece a b. |
| Requisitos funcionales: contribución individual diferenciada | Corresponde a c y a los registros humanos; e/g no acredita por sí solo esa contribución ni el pairing pendiente. |
| Evaluación: diseño (20 %) e implementación (30 %) | E01-E13/G01-G05 y E03-E13/E18, respectivamente. |
| Evaluación: DevOps y monitorización (20 %) | E17-E18 y G06/G09-G10, sin atribuirse la totalidad del apartado f. |
| Evaluación: negocio (10 %) | No se identifica cobertura adicional propia de e/g en la matriz suministrada; corresponde a b. |
| Extensión | Extracto local de cinco páginas; PDF nativo actual de 18 páginas comprobado por coordinación. Cumple el máximo de 20 en este corte, no en una versión definitiva aún incompleta. |

Los porcentajes anteriores conservan el desglose literal del guion: negocio
10 %, diseño 20 %, implementación 30 % y ejecución 20 %, que juntos componen
el 80 % de entregables; la presentación supone el 20 % restante. No se
normalizan esos pesos ni se atribuye a e/g la puntuación completa.

No se leen ni modifican apartados de otros responsables para completar esta
matriz. Las contribuciones generales y la evaluación global permanecen fuera.

## Fuentes técnicas y resultados acotados

Las referencias reproducibles de implementación son las especificaciones de
[ingesta](../../openspec/specs/advanced-document-ingestion/spec.md),
[chunking](../../openspec/specs/deterministic-document-chunking/spec.md),
[chat](../../openspec/specs/conversational-web-interface/spec.md),
[activación de RAG D](../rag-d-activation.md) y
[selección de modelos](../adr/ADR-0002-litellm-openrouter.md).
Los enlaces se interpretan sobre la base fijada, no como prueba de activación.

El paquete externo `jup063-verificacion-json-grafana-20261019/` conserva
`conciliacion-cifras.json`: 96 contrastes favorables y 272 hashes de JSON
originales de RAG comprobados. Se preservan los recibos y resultados fallidos.

| Evidencia | Resultado y límite |
| --- | --- |
| RAG A-D | 272 casos terminales: 267 respuestas, cuatro fallos y un rechazo previo 503. Cinco sin respuesta no significa cinco fallos de generación. |
| Valoración de D | 64 favorables, dos desfavorables y dos no clasificables sobre 68. Son juicios de Agente, no aceptación humana. |
| RAG E | 47/64 registros; campaña parcial y cancelada. Cambia también el chat: no permite atribución causal exclusiva al RAG. |
| Modelos del 19/10 | Mismo banco de 28 por modelo: 27 aceptables por Agente y un fallo 012 en ambos. GLM: 28 intentos; DeepSeek: 31, con tres truncaciones recuperadas. |
| Coste comparable de consultas | GLM 0,18059109 USD; DeepSeek 0,0391877208 USD. Incluye reintentos; excluye indexación inicial. No equivale a factura independiente por generación. |
| Tiempos de completadas | Mediana 13,375/15,469 s y p95 22,484/40,797 s (GLM/DeepSeek). No es tiempo al primer token. |
| Comparación de contenido | 24/27 textos y 18 JSON completos iguales. El código controla parte del resultado; no aísla capacidades puras de los modelos. |
| Grafana | El resumen incorporado conserva su corte histórico de dos runs y 84 filas. La ampliación local posterior (19 runs/510 filas) no sustituye esa medición ni acredita calidad semántica. |

La configuración de proveedor no demuestra qué infraestructura física atendió
una petición. Los datos son sintéticos; no acreditan ahorro real, seguridad
general ni beneficios en clientes. Las mejoras posteriores de recuperación no
heredan sin ensayo las valoraciones de campañas anteriores.

## Comprobaciones y pendientes

La preparación documental comprueba enlaces internos, hashes del extracto,
trazabilidad JUP, OpenSpec e higiene y controles de gobernanza aplicables.
Los recibos de ejecución y el diff se entregan separados al responsable de
publicación; no se presenta como ejecutada ninguna batería nueva de modelos.

Preparación local del 19/10: OpenSpec 1.8.0 estricto, 82/82; trazabilidad de diez
changes activos conforme; higiene conforme; 150/150 pruebas de los comprobadores
JUP, higiene, PR, CI y gobernanza. Se comprobaron 51 enlaces locales sin roturas
en los documentos afectados y los cuatro hashes de artefactos del manifiesto.
Los 96 contrastes suministrados son favorables; no se vuelven a ejecutar las
campañas originales para registrar este resultado.

Comandos nativos: `node tools/jup-check.mjs --all`,
`node tools/jup-cleanup-check.mjs`, `openspec validate --all --strict --no-interactive`
y `node --test tools/jup-check.test.mjs tools/jup-cleanup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs`.
En un checkout sin dependencias, la primera tanda dio 132 PASS y un fallo de
importación de `yaml`; se conserva como fallo de entorno. La repetición utilizó
OpenSpec 1.8.0 y yaml ya instalados, sin instalar ni modificar dependencias del
candidato. No hubo omisiones. Los resultados no sustituyen CI ni aprobación.

## Dictámenes locales y control de retorno

Sobre las ocho huellas del primer candidato documental sin commit, con la base
indicada, se recibieron los siguientes informes independientes. Las fechas y
horas son de Canarias; los originales permanecen fuera de Git.

| Dictamen local | Fecha del informe | Archivo y SHA-256 |
| --- | --- | --- |
| Revisión técnica: REVIEW_PASS, sin bloqueantes | 19/10/2026 18:26:00 | `jup063-documentary-review-20261019.md`: `f6ca921acdcfa2dff1d7f353c608582d9d5ce90b09817ec28f607b72ee76ada8` |
| Validación documental: VALIDATION_PASS, sin bloqueantes | 19/10/2026 18:29:19 | `jup063-documentary-validation-20261019.md`: `56352f6c86e259404eaaa1744fa4046fcbe2d9423ab2f530cf152a4800912152` |

Coordinación confirmó el retorno sobre las mismas referencias originales el
19/10 a las 18:30:47 y 18:30:49: ambos controles conformes y ocho fuentes externas
intactas. El delta de hitos y orden de archivo se evaluó después en r2;
sus adendas se conservan también fuera de Git:
`jup063-documentary-review-r2-20261019.md`, REVIEW_PASS
(19/10/2026 18:42:49), SHA-256
`fce15c52851b12623c3e90238ba83cbb292ae00e5f2d08cd75ae5938f59e0653`;
`jup063-documentary-validation-r2-20261019.md`, VALIDATION_PASS
(19/10/2026 18:42:42), SHA-256
`d06d759a7fc34fdd4524aa9379d4108adaf828e901372fbd3a6bcc8cfe7febb9`.
Estos dictámenes cubren sus huellas r1/r2, no se extienden unilateralmente a
esta actualización posterior de hechos. Su aplicabilidad se entrega con el delta.

Los dictámenes locales completan la evaluación técnica de ese candidato, no
los registros humanos del entregable ni las reviews humanas de PR #141.
Los dictámenes anteriores del paquete Grafana sólo cubren datos/configuración
y restauración; no se utilizan para aceptar el texto.

## Criterios de aceptación de la tarjeta

Los cinco criterios siguientes son los comunicados por coordinación tras leer
Trello el 19/10. Esta matriz no marca ni modifica la tarjeta oficial.

| Criterio de Trello | Evidencia local y estado | Registro externo o etapa pendiente |
| --- | --- | --- |
| Resultado funcional verificable. | Aportación e/g incorporada con aprobación; 28 párrafos exactos, dos tablas, fuentes y extracto fechado comprobados. Evaluación local r1/r2 completa; PDF nativo actual de 18 páginas comprobado por coordinación. | Aceptación humana final del entregable y extensión definitiva pendientes: c/h sin terminar, i parcial e índice global por actualizar. |
| Pruebas necesarias añadidas y en verde. | Controles documentales aplicables conformes: OpenSpec 82/82, trazabilidad, higiene, 150/150 pruebas y comprobaciones de fuentes. No hay producto nuevo que requiera otra batería. | CI del futuro commit/PR y adendas del delta actual, sin repetir campañas ni controles no afectados. |
| Documentación y decisiones actualizadas. | Evidencia, continuidad y contrato OpenSpec documentan la arquitectura vigente y sus límites; archivo autorizado ejecutado sin cambio semántico. | Control de composición y enlaces finales; no se introduce una decisión de producto nueva. |
| Pull request revisado y vinculado. | Aporte e/g preparado para la PR #141 existente, conservando sus commits y antecedentes. PR #95 cerrada sin integrar no acredita el cierre actual. | Publicar y vincular el aporte autorizado después del control independiente afectado; mantener las reviews humanas de #141 y revisar el nuevo delta sin atribuirlas como recibidas. |
| Validación funcional y evidencia enlazadas. | VALIDATION_PASS local, matriz de cobertura, fuentes y hashes del extracto documentados; no se afirma validación del producto desplegado ni de toda #141. | Registrar revisión y validación humanas del entregable en Doc y Trello con fecha/SHA, y enlazar el aporte y su evidencia en PR #141/tarjeta. |

Pairing humano: NO_ACREDITADO para este incremento. Persisten los comentarios
humanos Doc/Trello, reviews humanas de PR, versión final revisada y actualización
oficial. Paris ha autorizado cerrar esta entrega e/g y aportar su commit a
PR #141 por la excepción registrada; esto no acredita esas participaciones
ni cierra por sí solo la tarjeta.

Observaciones aprobadas para la PR: «c y h siguen pendientes; i está parcialmente
redactado»; «d describe una versión antigua del chat que debe armonizarse con
e/g». Son apartados fuera del alcance de esta redacción y no se modifican.
El índice global y la paginación definitiva se comprobarán al completar la
memoria. El PDF local de cinco páginas sigue siendo un extracto no nativo;
el PDF nativo de 18 acredita únicamente la extensión del corte actual.

Paris autorizó expresamente el 19/10 archivar esta entrega e/g y preparar una
PR borrador con los pendientes humanos visibles; después sustituyó la apertura
de una PR nueva por la integración autorizada en #141. Tras validar el change activo,
se archivó en 2026-10-19-jup-063-ai-memory y se promovieron los cuatro requisitos
de ai-memory sin cambio semántico. La CLI conservó el aviso de cuatro tareas
incompletas: pairing, comentarios humanos, exportación final y archivo aún no
marcado al iniciar el traslado. Sólo la tarea de archivo se completa después.
Las demás conservan su estado; archivar no acredita aceptación ni cierre.
La confirmación de la PR nueva queda obsoleta; la publicación del aporte en
#141 se rige por la excepción específica y los controles independientes y de CI.
Los comentarios humanos del entregable exigidos por la gobernanza no se
convierten aquí en una condición nueva anterior a abrir la primera PR.
No se modifica Trello ni se declara completada JUP-063.
