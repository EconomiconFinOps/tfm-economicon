# JUP-125 — Evidencia de chunking documental determinista

JUP: JUP-125 · [Trello](https://trello.com/c/H0RUnArf) · Registro: 16/10/2026.
[OpenSpec archivado](../../openspec/changes/archive/2026-10-16-jup-125-deterministic-document-chunking/proposal.md),
[diseño retrospectivo](../../openspec/changes/archive/2026-10-16-jup-125-deterministic-document-chunking/design.md),
[ADR-0023 Proposed](../adr/ADR-0023-deterministic-document-chunking.md) y
[runbook](../runbooks/document-chunking.md).

## Alcance, candidato y atribución

La implementación experimental del 15–16/10 y sus correcciones se formalizan
retrospectivamente: no se atribuye diseño OpenSpec anterior al código. PM
preservó el candidato R2 en `5dc6374743f66370c9f50ade1a73abc287d329e5`.
La rama normativa es `feat/JUP-125-deterministic-document-chunking`.
La incorporación `238963938e1947fe6d9e3a04900761683d11f6aa` añade JUP-124
`e126b21703a90dd7d03747a6b51bc4b5d246cf29`: seis rutas modificadas y ocho
documentos añadidos frente al manifiesto R2; sólo sandbox y su test cambian
producto. Las otras 1.640 fuentes anteriores son idénticas; no hay borrados.
Esta formalización modifica documentación, no código, tests, corpus o modelos.

JUP-124/PR #133 estaba en borrador al formalizar; se integró en develop el 17/10/2026 (`466b083a`) y la rama la incorpora en `4888625e`. PM
proporciona los hechos de CI y gestiona cambios de base. Una futura modificación
de bytes/base exige decisión de vigencia por cada evaluador; no hereda un PASS.

Roles humanos oficiales: Paris Arcos, liderazgo; Víctor Méndez, pairing;
Lucía Mateo, revisión; Alejandro Aguado, validación/pruebas/documentación.
Asignación no demuestra participación. Los informes locales independientes
identificados abajo no son las reviews humanas `Revision JUP-125` y
`Validacion JUP-125`; archivo, aprobación humana y publicación son pasos separados.

## Matriz de los quince criterios oficiales

La columna de resultado corresponde a evidencia previa identificada de R2,
revisada/validada localmente. La vigencia tras base/formalización se entrega en
informes nuevos separados. No se presenta una campaña histórica como nueva.

| Criterio | Evidencia histórica y alcance | Reproducción desde el repositorio |
| --- | --- | --- |
| 1. Normalizado y formatos sin reextraer | Nueve normalizados de extracción real identificada: MD/TXT/DOCX/DOC y PDF digital/tabla/OCR/mixto/híbrido. Grafo consume checkpoint, sin volver al original. | [estructura](../../apps/processor/tests/test_document_structure.py), [fixtures](../../apps/processor/tests/fixtures/normalized_documents), [reprocess](../../apps/processor/tests/test_reprocess_document.py). |
| 2. Tokens, 600/800 y overlap configurable | Contratos y tokenizer fijado; máximo incluye repeticiones, overlap efectivo registrado y cero entre secciones. Casos 0/0,1/0,9 y presupuestos alternativos. | [contratos](../../apps/processor/tests/test_chunk_contracts.py), [tokenización](../../apps/processor/tests/test_embedding_tokenization.py), [chunker](../../apps/processor/tests/test_structural_chunker.py). |
| 3. Unidades estructurales y fallback íntegro | H3–H6 que caben dentro de padre grande, tablas pequeñas/filas/celdas extensas, listas con padre/hijo y código por líneas; Unicode íntegro. | [chunker](../../apps/processor/tests/test_structural_chunker.py), [regresiones Markdown](../../apps/processor/tests/test_markdown_chunking_regressions.py). |
| 4. Regla y excepción juntas cuando caben | Regla relative_delta >20% AND absolute_delta >100 EUR/day junto a aclaración estricta; regla genérica distinta y control de subsección de 643 tokens. No algoritmo hardcoded. | [prueba de agrupación](../../apps/processor/tests/test_structural_chunker.py), [corpus real](../assistant-corpus/business-rules/economicon-mvp-rules.md). |
| 5. Identidad, contenido y procedencia | IDs/orden/tokens/hash reproducibles; spans y texto realmente coinciden, con páginas/líneas/coordenadas sólo disponibles. Unicode Markdown no desplaza rangos. | [contratos](../../apps/processor/app/embeddings/contracts.py), [reconstrucción y traza](../../apps/processor/tests/test_chunk_reconstruction.py). |
| 6. Fragmentos, repetición, versión y padre | Grupo/motivo/índice/total de registros persistidos tras omisiones; overlap/cabeceras explícitos. Padre conserva metadata documental. R2 incluye espacios interiores y negativos. | [chunker](../../apps/processor/app/embeddings/structural_chunker.py), [normalizado](../../apps/processor/app/embeddings/normalized.py). |
| 7. Determinismo | Repetición exacta de resultados y seis casos comparativos completos idénticos, incluidas metadata/manifiestos; 46 inputs y 5.839 tokens iguales. No fechas/modelos para decidir cortes. | [casos deterministas](../../apps/processor/tests/test_structural_chunker.py), [identidades](../../apps/processor/tests/test_chunk_contracts.py). |
| 8. SQL y generación atómica | PostgreSQL/pgvector real: migración JSONB aditiva, rollback tras DELETE, CAS, concurrencia y dimensión. Padre/chunks/vectores coherentes. | [publicación](../../apps/processor/tests/test_chunk_publication_pgvector.py), [migración 003](../../apps/processor/app/vector_store/migrations/003_chunking_metadata.py). |
| 9. Legacy, coexistencia y tenant | SQL real mantiene filas/IDs/texto/metadata/vectores previos a003, añade chunks reales y recupera/cita ambos. Vecino extranjero excluido antes del límite. Reprocess exige propietario/tenant/checkpoint; no masivo. | [coexistencia y retrieval](../../apps/backend/tests/test_tenant_isolation_vector.py), [reprocess](../../apps/processor/tests/test_reprocess_document.py). |
| 10. Todos los formatos desde extracción real | Fuente, JSON extraído y fixture verificados por hash 9/9; métodos reales de fase1 identificados. No se utiliza corpus manual comparativo como extracción. | [nueve fixtures congeladas](../../apps/processor/tests/fixtures/normalized_documents), [pruebas actuales](../../apps/processor/tests/test_chunk_reconstruction.py). |
| 11. Reconstrucción sólo chunks y negativos | 36 pruebas de reconstrucción; nueve formatos, Unicode/blancos, overlap/cabeceras, tablas/listas/código. Mismo TXT de 200.013 caracteres recuperado en dos chunks/max600. Ausencia/duplicación/corrupción fallan. | [reconstrucción](../../apps/processor/tests/test_chunk_reconstruction.py), [función y límites](../runbooks/document-chunking.md#reconstrucción-exacta-desde-chunks). |
| 12. Texto y citas realmente trazables | Contraste exacto chunk↔normalizado y bloque/filas/celdas; páginas/líneas/bbox disponibles, multipágina y ausencias honestas. Flujo SQL de nueve formatos contrasta citas emitidas con metadata persistida. | [traza](../../apps/processor/tests/test_chunk_reconstruction.py), [citas y snapshots](../../apps/backend/tests/test_tenant_isolation_vector.py). |
| 13. Validación antes de persistir | Cobertura/orden/IDs/hashes/rangos/repetición/grupos incompletos rechazados; desconocimiento estructural declarado como tal. R2 no relaja función ni negativos previos. | [negativos](../../apps/processor/tests/test_chunk_reconstruction.py), [publicación](../../apps/processor/tests/test_chunk_publication_pgvector.py). |
| 14. Comparación y límites honestos | Corpus congelado de seis documentos/doce preguntas, 46 vectores reales de1536D; Recall@1/3/5/10=12/12 ambos,25→9 chunks. Escala20MB:8417chunks/max800/reconstrucción exacta12,18s con2CPU/2GB. No mejora general ni garantía de producción. | Baseline [TextChunker](../../apps/processor/app/embeddings/chunker.py), contrato actual y [metodología/límites](../continuidad/chunking-documental.md). Artefactos congelados bajo custodia del liderazgo. |
| 15. Contratos, preparación/docs y evaluación | Modelo/proveedor/dimensión/coseno/ranking/prompts intactos. cl100k_base externo preparado y runtime offline, GLM separado. README/runbook/continuidad y evaluaciones independientes; CI y humanos diferenciados. | [preparador](../../apps/processor/build_tokenizer.py), [processor](../../apps/processor/README.md), [runbook](../runbooks/document-chunking.md). |

Las cuatro comprobaciones expresas de Paris se corresponden respectivamente con
9 (legacy real), 1/10 (formatos realmente extraídos), 11 (reconstrucción sólo
chunks) y 5/12 (correspondencia textual). No se aceptan por mera presencia de campos.

## Campañas anteriores y huellas de originales

- Núcleo final R2 del principal: 175 PASS; Revisor: 175 propios; Validador:126
  afectados propios (36 reconstrucción,50chunker,40Markdown). Se solapan: no se
  suman como pruebas únicas. Ambos reprodujeron el mismo input200kespacios, SHA256
  `a3a0b0d702dccc183c6921973ff594c0b1c3e61c418ca60310efe14203a9cd4a`,
  exit0/doschunks/máximo600. Son campañas locales del16/10, no CI remota.
- REVIEW_PASS R2 original: SHA256
  `97854e622268a28218d1b677b8029df36f52b02b6eb630b52824abc5fc2e59fd`.
  VALIDATION_PASS funcional R2 original: SHA256
  `b923905e8bad8ad002cc3377d87fb54ea28b01452283eede86dfc2ee4194d461`.
  El Validador además ejecutó SQL real de nueve formatos, reconstrucción sólo
  desde filas, citas y equivalencia propia completa del lote comparativo.
- Los FAIL finales previos siguen intactos: revisión SHA256
  `4391c512eec2b9adfc5067afbf38b49071923c67225e9747dceb029339e95b6f` y
  validación SHA256 `2528c100315a8533f655b87bbb9f087e114ce7bc839473703c5c03b0e3e00116`.
  R1TXT, A/B y R2 conservan pruebas y correcciones, no se reescriben como PASS.
- PM leyó íntegros los originales y verificó las MISMAS referencias R2 a
  09:39:11/12UTC, exit0/ok:true/violations:[], recibo SHA256
  `3f6df05c153ebd7affbf2be1a9d906e2cf1c5df1305fb5d967578fd63d97130e`.
  El manifiesto de ese candidato era SHA256
  `5001fc832e9b2dccecb3002d0a6485860dbfb54026d7bceff61f18a8999e1fa4`;
  no se utiliza como guarda de la base/documentación nueva.
- SQL de la ronda final anterior:23backend+18processor PASS propios por rol;
  doctor59/59 en una corrida propia de cada evaluador. La evidencia no afectada
  se reutilizó con justificación individual; no se atribuye otra campaña general.
- Comparación real congelada: SHA256 del corpus
  `1db07751e61e841cfb00d6cd5d5b5aac1b5d989b9e2de7fe92840effeddd030b`.
  46inputs/5839tokens reales ya pagados; las regeneraciones finales mantuvieron
  contenido/IDs/metadata/manifiestos exactos. Caché, tokenizadores, corpus
  comparativo externo, logs e informes se conservan fuera de Git bajo custodia
  del liderazgo, sin rutas personales o credenciales en esta evidencia.

## Base incorporada, formalización y comprobaciones actuales

El arreglo de extracción de JUP-124 permite sólo lectura/ejecución de las rutas
Python stdlib/platstdlib/purelib/platlib declaradas por sysconfig; no abre todo
el prefijo ni desactiva el sandbox. Su test conserva controles de red/archivo
ajeno y ruta explícita del hijo. Evidencia fase1 atribuida:25pruebas propias del
principal y del Revisor; Validador recorrió nueve formatos con S3/cola/SQL/OCR
reales y46comprobaciones, inferencia mock. No se ejecuta OCR completo por rutina
al formalizar chunking. Véanse [JUP-124](JUP-124-validation.md) y su runbook.

PM informa al16/10: pushfase1 e126b217 con6/6comprobacionesPASS y processor de
PR133 PASS; evento PR backend con6FAILhealthJUP047,2233PASS/293skips. Diagnóstico
atribuido a fase1: JWT creados al importar caducan antes de ejecutar el caso;
corrección focal sólo de tests evaluada aparte. PM incorporó
`eb4453f96b7bab819bf4ba692e6bdcf7e521f2ef` mediante
`2bf31fe356aeccc45991c9f91d65dfbba29b003d`. Sólo cambia
`apps/backend/tests/test_system_health_jup047.py`, SHA256
`8c7ac6d3b1726c3afdbde619255ff2ff5510434a650a55c0f1bbbe54233e3acd`;
las otras 1.660 fuentes y los trece documentos de formalización se conservaron.
Los JWT se emiten al actuar en cada caso, sin cambiar TTL/leeway/auth/runtime.
Ocho variantes propias afectadas pasan sobre esa base, 25 no seleccionadas y
144 avisos datetime SQLite conocidos. No se ejecuta una batería backend completa.
Los datos CI de e126b217 son el contexto previo atribuido; no se afirma CI remota
del nuevo HEAD. No se extienden las guardas anteriores a estos bytes.

Controles propios de esta formalización del 16/10: change estricto válido y
75/75 items OpenSpec globales con CLI fijado 1.8.0; trazabilidad de JUP-125 y todos
los changes; higiene de 1.661 fuentes; diffcheck limpio; 97 pruebas nativas de
trazabilidad/higiene/política PR/CI/gobernanza; 184 enlaces locales de doce documentos.
El primer control de enlaces conservó dos destinos ausentes preexistentes del
índice. Se corrigieron sólo sus rutas hacia JUP-068/JUP-017 versionadas, preservando
conclusiones/fechas; repetición 184/184 sin errores. No se verifican sitios remotos.

Consumidores directos de la nueva base: tres pruebas propias TXT/Markdown y
sandbox en Linux, sin privilegios, sin red y con fuente RO: 3 PASS, 15 casos no
seleccionados. No se llama a esos 15 una nueva validación ni se repite OCR.
Antes de la incorporación health, las 739 fuentes no documentales anteriores
a esta formalización conservaron bytes. Después, 738 permanecen idénticas y la
única diferencia es el test health evaluado por separado, con su hash contrastado.
El principal no modifica código ni tests. Herramientas/dependencias temporales
externas; no entornos o tokenizadores en Git. La base final es `2bf31fe3`. Revisor y Validador deben decidir vigencia de base/documentación
con originales y guardas PM nuevas. No se anticipa su dictamen ni se archiva aquí.

## Reproducción y límites

Seguir el [runbook](../runbooks/document-chunking.md) con entorno propio Python3.12,
dependencias declaradas y tokenizer preparado fuera del checkout. Núcleo:

```text
cd apps/processor
python -B -m pytest -q tests/test_chunk_contracts.py tests/test_embedding_tokenization.py tests/test_document_structure.py tests/test_structural_chunker.py tests/test_reprocess_document.py tests/test_markdown_chunking_regressions.py tests/test_chunk_reconstruction.py
```

Desde raíz: `corepack pnpm openspec:validate`, `corepack pnpm jup:check:all` y
`corepack pnpm jup:cleanup:check`. Las pruebas SQL y el smoke se describen en el
runbook y requieren recursos desechables, opt-ins y credenciales sintéticas;
ninguna receta autoriza uso de bases compartidas o gasto nuevo.

Los datos8D/mockagente demuestran integración/SQL, no calidad semántica. La muestra
real1536D es exploratoria; no acredita producción, todo OCR posible ni mejora
general de Recall. Las citas históricas son snapshots; legacy sin descriptor no
promete reconstrucción exacta. Se recupera texto normalizado, no layout/binario.

El intento anterior de descarga GLM falló por SHA/tamaño; se preserva como límite
de preparación, no build productivo actual favorable. Pin/preparadorGLM intactos,
pruebas previas reutilizadas por mecanismo no cambiado. Las baterías generales
anteriores conservan originales con fallos y repeticiones focales; no se declara
una fullsuite nueva limpia ni una CI global favorable por estos resultados.

Coste del único lote previo:0,00011678USD, conciliado por liderazgo0,0001041934EUR
dentro de0,10EUR autorizados. Rondas finales/formalización sin nuevas inferencias.
Recursos propios de campañas anteriores retirados; cualquier infraestructura de
esta formalización se inventaría y retira aparte, sin copiar datos/cache al repo.


## Evaluación final, control PM y autorización de archivo — 16/10/2026

Sobre `2bf31fe356aeccc45991c9f91d65dfbba29b003d` más las trece rutas
documentales locales (1.661 fuentes, digest
`e19657e8314b80bea6cf1da94d1cb625bbdbf79530f5b16b45c528df544cc4bf`),
la reevaluación independiente final concluye **REVIEW_PASS** técnico y
**VALIDATION_PASS** funcional. Cada rol conserva individualmente la vigencia
de los quince criterios y las cuatro comprobaciones expresas. Los once casos
afectados por rol (tres extracción/sandbox y ocho health), OpenSpec 75/75,
184 enlaces, trazabilidad e higiene son comprobaciones propias de esa ronda;
las campañas funcionales anteriores no se presentan como repetidas.

Original Revisor SHA256
`90b62e4ad8b8fb0248a849f9d109b961b4048b04db513449db1c6f9bfe00aa25`;
original Validador
`a5d097ccf54ee63d78ec52604679f28e123e96510eddb88dea7706185a8f233b`.
Entrega consolidada SHA256
`2716cdc5a210d5fdfce3ac1c78a81c2279dcd88a87b465c1d42fc473d39df865`.
Los originales adversos y sus bases se conservan; no se eliminan por el cierre.
PM leyó íntegros los informes, contrastó sus hashes y verificó las MISMAS
referencias originales de ambos roles, sin violaciones, a11:11:22/24UTC y
otra vez antes del archivo autorizado. Es detección de estado final, no
certificación de aislamiento técnico absoluto o escrituras restauradas.

Recursos propios retirados: tres imágenes auxiliares comprobadas porID/etiqueta,
cero consumidores/recursos activos; corpus y46entradas de caché intactos.
No hubo nuevas inferencias o gasto. Siguen vigentes los límites deGLM/build,
modelo mock y muestra exploratoria descritos en esta evidencia.

La dependencia JUP-124/PR133 tiene CI7/7 y SQL correctos sobre `eb4453f9`:
[CI](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38889949590),
[SQL](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38889949613).
No es CI propia de esta rama. PR133 seguía en borrador/no integrada al aprobar
este archivo; la rama conserva esa dependencia.

**Aprobación posterior a validación:** Paris Arcos acepta el cierre y autoriza
expresamente el16/10/2026 archivar este OpenSpec, hacer commit/push y comprobar
la CI de fase2. Pide ver el mensaje de la PR ANTES de publicarla; la publicación
no queda autorizada por esta decisión. El DoD local con el change aún activo
y las verificaciones originales quedan conservados por el liderazgo.

El archivo y los enlaces posteriores son cambios documentales autorizados;
no modifican código, tests, contratos funcionales ni las fuentes evaluadas.
Después del traslado se ejecutan las comprobaciones nativas documentales y
de trazabilidad sobre la disposición archivada, sin fingir una nueva ejecución
contra el directorio activo desaparecido. ADR-0023 sigue Proposed. Pairing,
reviews humanas, CI propia, publicación y merge son hitos separados.


## Reconciliación con develop mediante la dependencia de fase 1 — 17/10/2026

Preparación local autorizada sobre `0d34c06b1e381e2388bc310e0ba814ad961677e7`
con `d4c545e7462b4fbd54dfc6e05dc74e20367a9e1b` de JUP-124, que incorpora
develop `ffdd8ee9895d95e085ef31f18064fd55d56fe4e5`. Se conservan el archivo
OpenSpec ya existente y ADR-0023 Proposed; no se realiza otro archivo ni se
atribuye integración en develop. Los hechos oficiales y el feedback proceden
del paquete fechado del liderazgo: PR134 en borrador, sin comentarios/reviews/hilos
en el corte; el refresco de la tarjeta falló y no se presenta como lectura nueva.

Sólo hubo conflictos en los índices ADR y continuidad: se unen las filas de
chunking, ingesta y dashboard. Se conservan los dos ADR-0022 con sus rutas y
estados originales, sin renumeración. La combinación automática del pipeline
mantiene `normalized_document` como entrada del grafo y lo retira del resultado,
junto con los controles de revocación y propiedad de la ejecución de fase 1.
No cambia el algoritmo de chunking ni sus fixtures, metadata, reconstrucción,
reprocesado, publicación vectorial o citas. Se incorporan los fixes de pairing
de fase 1 y la compatibilidad CD de Grafana sin rotación, MinIO y CI combinados.

Comprobaciones propias de este hito, separadas de las campañas históricas:

- Herramientas doctor/smoke/topología/CI: 128/128 PASS, Node24.22.0, yaml2.9.0,
  candidato y dependencia RO, sin red. El smoke usa adaptadores de prueba;
  no representa una nueva pila de ingesta.
- Processor: primera selección 332 PASS, 6 FAIL de subproceso y 6 SKIP SQL
  optativos. El diagnóstico reprodujo `ModuleNotFoundError: structlog` porque
  el subproceso sustituye PYTHONPATH y no veía las dependencias externas.
  Se montaron las mismas dependencias declaradas en site-packages y se añadieron
  las declaradas del backend necesarias; los seis casos afectados pasan después
  (6 PASS, 6 variantes SQL no seleccionadas). No se cambia código ni prueba
  para obtener PASS, ni se presenta una nueva corrida completa de 338.
- La selección anterior incluye el chunker real sobre nueve normalizados
  congelados de extracción, reconstrucción sólo desde chunks y negativos,
  rangos Unicode/subsecciones, límites 600/800/10%, checkpoints y reprocesado.
  Los 764 avisos iniciales y 38 de la repetición son del adaptador datetime
  SQLite de Python3.12. No se habilitaron las seis variantes de Cockroach:
  sus fuentes/contratos SQL no afectados conservan la evidencia real anterior.
- CD: 2/2 PASS con Compose real, raíces nueva/heredada, ambas ranuras,
  propagación de contraseña Grafana, preservación/idempotencia y MinIO.
  Sin up, despliegue o DockerServer.
- Assistant entrante: 29/29 PASS. OpenSpec estricto: 77/77 PASS.
  Trazabilidad de los ocho changes activos correcta; higiene correcta.
  Mientras dos entradas siguen UU para staging PM, el checker cuenta cuatro
  stages adicionales; el manifiesto final deduplica los archivos.
- Diff propio frente a d4c545e7 sin avisos. Frente al primer padre conserva
  dos avisos entrantes de develop (spec de dashboard y test de sus queries),
  identificados en la evidencia de fase 1; no se reparan por arrastre.

Vigencia de las cuatro comprobaciones expresas: legacy recuperable y coexistencia
SQL se reutilizan por identidad de stores, migración003, citas y pruebas; no es
otra consulta SQL real. Los nueve formatos, reconstrucción y traza textual se
ejercitan de nuevo en los tests existentes sobre sus normalizados congelados,
sin reextraer ni repetir OCR. Las pruebas históricas SQL de citas/tenant y la
comparación de 46 vectores mantienen su atribución anterior, sin una nueva
campaña de calidad ni mejora general inferida.

Python3.12/Linux propio con dependencias declaradas resueltas para este ensayo;
no se afirma identidad con requirements.lock ni build productivo. Se conserva
inventario de versiones externo. Tokenizer tiktoken0.14.0/cl100k_base preparado
con la herramienta existente fuera de Git, 1.681.126 bytes y SHA256
`223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`;
runtime sin red. Se conservaron los incidentes de preparación (instalación aún
copiando archivos, Git ausente en imagen Node y shim Windows inexistente) y sus
resoluciones de entorno; ninguno se oculta como resultado de producto.

Las resoluciones y documentación esperan staging/commit PM. Después se requieren
dictámenes nuevos de Revisor y Validador distintos contra referencias PM nuevas,
sin extender los PASS anteriores. CI propia de 0d34c06b es histórica; la CI del
futuro commit, aprobación humana, pairing de Víctor y reviews de Lucía/Alejandro
siguen separados. Sin nuevas inferencias, proveedores, gasto, fase3 o cálculos.
