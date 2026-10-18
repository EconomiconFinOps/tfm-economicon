# PR140: reconciliación local tras PR133

Verificado: 2026-10-17. Origen: encargo de Sala de Control
`01a1270c-e332-7462-9c90-706d49ade92c`, atendido en
`01a143ae-b740-7043-aedb-1a8a65b4b585`. Estado: resolución comprobada;
publicación autorizada para desbloquear la revisión de Víctor. CI/SQL y nuevos
dictámenes del SHA publicado se registrarán en la conversación de PR140.

## Entradas y alcance

- [PR140](https://github.com/EconomiconFinOps/tfm-economicon/pull/140):
  `09b3c8bb3c113628adf35c324577ac3128a82423`, delta publicado de las cinco
  [correcciones de Víctor](../evidence/JUP-123-victor-corrections.md).
- `develop`: `466b083a6dae97f418cfb1d9156325749c6d7304`, squash de
  [PR133](https://github.com/EconomiconFinOps/tfm-economicon/pull/133).
- Base común: `1de41b907f849082b0676319971775a6560b71b5` (PR131 integrada).
- Checkout propio: `tfm-economicon-pr140-reconcile`, rama
  `fix/JUP-123-local-reconcile`. Publicación en la rama existente de PR140,
  `feat/JUP-123-chat-quality-delivery`, mediante avance normal, sin forzar historia.

No se incorpora PR134, PR139 ni el candidato `cd2bab7f` de PR135.
PR138 es un seguimiento documental independiente; B permanece en PR140.
La primera fase local `f9d376c8` se cerró sin push ni solicitudes de revisión.
La continuación autoriza publicar esa composición, sin merge a develop ni campaña
de inferencia. El único cambio posterior a las pruebas focales es esta documentación.

## Conflictos y resolución

Sólo dos conflictos de texto. Hay cuatro rutas modificadas por ambas entradas:

| Ruta | Causa y resolución |
| --- | --- |
| `apps/backend/tests/test_system_health_jup047.py` | Ambas ramas posponen la creación del JWT hasta ejecutar cada prueba, evitando su caducidad durante collection. PR133 añade IDs explícitos a los cuatro casos. Se conserva exactamente el archivo de PR133: mismos códigos 401/400/403/400 y credencial creada durante ejecución. |
| `docs/continuidad/README.md` | Inserción de ingesta frente a actualización del colector/B. Se conservan la entrada de ingesta y el estado más reciente del colector; se distingue el publicado 09b del candidato local. |
| `apps/processor/requirements-dev.txt` | Automerge sin conflicto: conserva `jsonschema==4.25.1` de B y `reportlab>=4.4,<5` de PR133. |
| `docs/adr/README.md` | Automerge sin conflicto: conserva el enlace corregido de Grafana, el ADR de ingesta y el ADR0023 del modelo de B. |

No se modifica producción para resolver conflictos. La comparación de blobs del
índice conserva exactamente las 66 rutas exclusivas de PR133 y las 206 exclusivas
de B, además de las rutas de las cinco correcciones salvo los registros compartidos
reconciliados arriba. Incluye archivos eliminados por el archivo OpenSpec.
La duplicación de número ADR0022 (Grafana/ingesta) ya existe en `466b083a`;
se preservan ambos destinos, sin renumerar documentación ajena en este delta.

La excepción de archivo técnico OpenSpec autorizada expresamente por el usuario
permanece en las tareas archivadas y en la evidencia de correcciones. No transforma
aceptación pendiente en completada ni constituye autorización de merge.

## Pruebas propias del árbol combinado

Linux, Python 3.12, contenedores temporales propios sobre imágenes de dependencias
de PR133 más `jsonschema==4.25.1`; fuente montada de sólo lectura, sin red durante
pytest, sin servicios externos ni inferencias. Fuente comprobada mediante SHA256
antes y después; contenedores, imágenes derivadas y temporal retirados.

| Selección | Resultado |
| --- | --- |
| Backend: `test_system_health_jup047.py`, `test_migration_reconciliation_jup035.py`, `test_document_uploads.py` | 67 PASS |
| Processor: `test_chat_guards_jup123.py`, `test_chat_shared_modules_jup123.py`, `test_chat_quantity_work_jup123.py`, `test_chat_savings_realization_jup123.py`, `test_document_checkpoint.py`, `test_document_markdown_lines.py` | 92 PASS |
| OpenSpec `validate --all --strict --no-interactive` | 78/78 PASS |
| `node tools/jup-check.mjs --all` | PASS, nueve changes activos |
| `node tools/jup-cleanup-check.mjs` | PASS, 1.924 archivos incluido este resumen |
| `git diff --cached --check` y rutas sin resolver | PASS, ninguna ruta sin resolver |

La primera invocación de higiene no pudo iniciar Git por EPERM del sandbox;
la repetición con permiso de proceso pasó. Las advertencias SQLite/fork de pytest
se conservan en los logs. Los fallos iniciales del arnés de inventario fueron
corregidos (cuarta ruta compartida y archivo eliminado); no fueron fallos del producto.

Evidencia externa al repositorio, relativa al workspace Economicon:
`materiales/07-evidencias/JUP-123-collector/PR140-reconcile-466b083a-20261017/`.
Contiene inventario y tres etapas de cada conflicto, `source-preservation.json`,
`check-source.py`, `linux-focal.py`, `linux-focal.json` y logs por servicio.

## Límites y validación final mínima

La CI y SQL de 09b conservan su identidad histórica; no son resultados del merge
local. Tampoco se trasladan aquí las aprobaciones de PR133 ni la N5 histórica de
f3ec760d. No se tocan sus 497 evidencias congeladas, ledger, reservas o contadores.
No se reclama cobertura nueva de pgvector, OCR real, navegador ni calidad con modelo.

La espera propuesta tras PR135 queda superada por la petición concreta de Víctor
de resolver los conflictos para revisar (Discord `1561132947539492875`, 17/10 a
las 21:44:59 UTC) y la instrucción de coordinación de publicar. No era una
dependencia técnica ni un orden de merge aceptado. Se verifican de nuevo las
referencias remotas: PR140 permanece en 09b y develop en 466b; no hay delta nuevo.

1. Publicar la composición ya comprobada tras revisar diff, trazabilidad e higiene.
   No repetir los nueve archivos focales porque sólo cambia esta documentación;
   los blobs de producto y pruebas son idénticos a `f9d376c8`.
2. Ejecutar CI técnica y SQL sobre el SHA publicado y enlazar resultados exactos.
   El SQL cubre CockroachDB; no pgvector ni calidad de modelo.
3. Con candidato coherente y checks conformes, conservar la petición oficial a
   Víctor si sigue abierta y pedir a Lucía revalidar el delta de integración una
   sola vez. Su APPROVED `5560194926` corresponde a 09b, en mock y sin nueva N5,
   pgvector ni UI; no se traslada automáticamente al nuevo SHA.

La revisión de integración debe comprobar la conservación de las cinco
correcciones de 09b, los dos conflictos resueltos y la coexistencia de ingesta/chat
en configuración, arranque, migraciones, dependencias y cola. No requiere otra N5.
Un cambio futuro de develop tendrá su propio inventario y selección de pruebas.

La continuidad de B y sus límites de aceptación siguen en
[evaluación local](chat-evaluacion-local.md); la implementación de PR133 está en
[ingesta documental](ingesta-documental.md).
