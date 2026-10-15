# JUP-065 — Validación de la preparación de demo

Fecha: 2026-10-01. [Trello](https://trello.com/c/SZUFo4ol).
PR [#63](https://github.com/EconomiconFinOps/tfm-economicon/pull/63).
Rama: `docs/JUP-065-functional-demo`, sobre develop
`de0d62e7c0028f35a81c5087f531d19031a90e81`.
[Paquete](../demo/JUP-065/README.md) y
[alcance OpenSpec](../../openspec/changes/archive/2026-10-03-jup-065-functional-demo/proposal.md).

## Actualización tras la revisión complementaria de Lucía — 15/10/2026

Se reconcilia f27eb7f con develop53b43bb1e79b08967cc1b9efdf66669f11e8197c.
El conflicto del índice conserva las entradas de ambas ramas; CI mantiene todos
los comandos de develop, las tres comprobaciones de demo y el historial Git.
No hay cambios propios de producto, configuración o dependencias frente a develop.

Atendidas las observaciones del14/10: JUP-119/demo_data sustituye JUP-106,
se evita cargar Core/Growth con el perfil demo, se explica status/remove sin
--tenant y se prefieren volúmenes propios nuevos. Se incorporan HMAC, subred,
backend-migrate, CHAT_ENABLED y el panel lateral con sus etiquetas actuales.
Guion, puertas A/JUP-122 y B/JUP-123, preflight y plantilla quedan alineados.
PR130/A y PR69/JUP-036 integradas; B en curso, sin aceptación. La nueva evaluación
N3 que registra Trello no se presenta como finalizada ni validada.

Verificación propia offline sobre esta combinación:

- Verificador normal y optimizado:15/15; artefactos sin cambios respecto a f27eb7f.
- Tres tests de integridad PASS. El nuevo caso regenera ambas copias con un grupo
  adicional y exige rechazo por invariante. Sustituir require por no-op sólo en
  memoria hace fallar ese test (ValueError no lanzado); verificador sin cambios.
- Banco fijado:28 preguntas/7 categorías. Gobernanza completa:34 comandos exit0.
- OpenSpec estricto:74/74;19 enlaces locales del paquete correctos;diff sin errores.
- Tres omisiones locales:una de pgvector y dos de CD dependientes de Linux.
  No se ejecuta runtime, Docker, navegador, proveedor ni ensayo integrado.

Logs locales:materiales/07-evidencias/JUP-065-actualizacion-2026-10-15/ del workspace.
El corpus fijado no equivale al corpus actual JUP-129: índice/corpus/embeddings
requieren validación en el entorno final. No se atribuye validez generativa a mock.
Víctor validó f27eb7f el11/10 y Paris aprobó el13/10; esos dictámenes no acreditan
este incremento. Pendientes CI del SHA publicado y revalidación incremental de
Paris/Víctor, pairing y ensayo. Los resultados finales de CI se enlazarán en PR63.

## Preparación reconciliada — 11/10/2026

Corte nuevo que sustituye el estado de preparación del 10/10, sin convertir las
pruebas históricas en ejecuciones actuales. Origen: «Adelanta JUP-065 — Preparar
demo funcional del MVP», chat `01a12c49-7488-72f0-9077-1137c5c4f2a6`.

GitHub confirmó PR63 OPEN/CONFLICTING en `af132c1`. Se leyeron las 14 reviews,
los cuatro comentarios de conversación y la lista inline vacía. Paris publicó
[Revision favorable de af132c1](https://github.com/EconomiconFinOps/tfm-economicon/pull/63#pullrequestreview-5483308218)
el 11/10. Víctor conserva su dictamen sobre `a75b707`; ambos son evidencia de
sus versiones, no de la nueva combinación. No se cambian roles ni se extienden
las excepciones de otras tareas.

Reconciliación desde `af132c11019319258233f00523cb1d12453da122` con develop
`3b8e95288000b1f14513cbc5158324017554f514` en el checkout aislado limpio de
JUP-065. Dos conflictos resueltos: CI conserva la unión de comandos de ambos
padres, incluidos business-metrics y demo/historial completo; índice conserva
todos los temas y fechas. Sin cambios propios de producto/configuración,
infraestructura, dependencias, AGENTS o CONTRIBUTING frente a esa base.

Guion aclara cómo acreditar 38 registros; preflight incorpora consulta SQL de
jobs por tenant/UUID, escenario normal explícito y prevención de cargas previas.
README diagnostica el objeto Git ausente sin cambiar el generador.
[Procedimiento integrado](../demo/JUP-065/ensayo-integrado.md) y plantilla cubren
prerrequisitos JUP-035/036, secuencia, respuesta/cita/rúbrica, tramo de costes,
reproducción independiente y aceptación pendiente. No se implementan 035/036.

**Comprobaciones propias**, Windows, Python 3.14.4 / Node 24.14.1:

- Integridad normal/optimizada: 15 archivos idénticos; dos tests negativos pasan;
  28 consultas/siete categorías. Originales no regenerados.
- Los 31 comandos del paso de gobernanza del workflow pasan (exit 0), incluidos
  99 tests focales, OpenSpec 63/63 y seis changes trazables. Once omisiones:
  calibración pgvector 1, costes sintéticos SQL 8, CD POSIX/Linux 2. No son pruebas
  de base real ni de despliegue. Higiene 1188 en el corte anterior a añadir este recibo.
- Diez fuentes fijadas coinciden por SHA-256 con develop; quince artefactos y tres
  scripts conservan blobs de af132c1. DEFAULT_DEFINITION coincide con la consulta
  fijada; junio completo selecciona las mismas 40 filas, última fecha 19/06 y suma
  exacta 0.060113199075769. Es contraste estático/offline, no ingesta nueva.
- Dieciséis enlaces del paquete comprobados y diff propio sin errores.

[Recibo estructurado](JUP-065-preparation-20261011.json). Logs y fuentes de
GitHub/Trello: `materiales/07-evidencias/JUP-065-preparacion-2026-10-11/` del
workspace, fuera del repositorio. Los errores iniciales de permisos del sandbox
se resolvieron repitiendo los checks con permisos aprobados y temporales propios.
Los tests CI siguen teniendo los límites ante desactivaciones deliberadas ya
anotados por Víctor; conservar comandos no equivale a un control de seguridad.

Trello leído sólo por DockerServer, snapshot `snapshot-20261011T184737Z.json`:
JUP-065 mantiene roles Alejandro/Lucía/Paris/Víctor y estado 50; JUP-035/036
conservan su trabajo pendiente. La descripción antigua de la tarjeta no es un
estado actual del head; el nuevo recibo se enlaza tras publicar.

**Pendiente:** CI remota del SHA que contiene esta sección (consultar PR63),
revisión/validación incremental de lo afectado, pairing Lucía, entorno/consumo
autorizados y ensayo integrado con JUP-035/036, modelo real/citas/rúbricas/duración y
reproducción independiente. El runtime parcial con mock de Víctor en bf50073/
b77d596 mantiene su fecha y límites; no valida esta base. Registro `not_run`.
Sin merge, cierre, despliegue, pago de modelos, Discord ni reviews inventadas.

## Histórico: reconciliación con develop — 10/10/2026

Preparación reconciliada desde `48ee74250714c6fe50946906824b80dc9ffd59fa` con
`develop` `412ae411c7f3a9b51f65407974962ac2b4545686`, por Alejandro a petición del usuario.
Único conflicto: `docs/continuidad/README.md`; conserva todos los temas entrantes,
la fila de demo y la fila histórica de presupuestos. CI conserva los tres comandos
de demo e historial completo, e incorpora los controles actuales de develop,
incluidos evaluación, contribuciones y ejecución directa de tests frontend.

JUP-037 introduce un modo de consultas estructuradas en el chat. README, guion y
preflight explicitan mantener desmarcado «Consultar costes por propiedad» para
los prompts documentales de la demo. Los quince artefactos y los tres scripts de
preparación/integridad conservan sus blobs respecto de `48ee742`; no se regeneran
los originales ni se modifica su commit fijo. No hay cambios propios en producto,
Compose, variables de entorno, paquetes, infraestructura o scripts frente a develop.

Comprobaciones propias en Windows, Python 3.14 y Node 24.14.1:

- Integridad offline: 15 archivos reproducibles; dos tests con casos negativos pasan.
- Preguntas: 28 consultas / siete categorías, fuentes y rúbricas correctas.
- CI/política/gobernanza/trazabilidad/higiene: 99 tests pasan; ocho changes trazables,
  higiene de 1061 archivos y `git diff --check` correctos.
- OpenSpec estricto: 58/58 elementos, sin fallos.

La primera ejecución restringida encontró denegaciones de procesos/temporales del
sandbox; las comprobaciones afectadas se ejecutaron después con permisos aprobados
y temporales propios. No se atribuyen esos errores al producto. Logs y recibos
locales en `materiales/07-evidencias/JUP-065-estado-2026-10-10/`, fuera del repositorio.

Estos resultados comprueban la preparación, no son reviews humanas. Paris revisó
favorablemente `48ee742` el 09/10; Víctor conserva su dictamen histórico en `a75b707`.
La combinación nueva requiere revisión/validación incremental de lo afectado.
Pairing Lucía, CI remota del nuevo commit, ensayo integrado, proveedor real,
ingesta/SQL, navegador, citas, duración y reproducción independiente pendientes.
El registro de ensayo permanece `not_run`; no se cierra JUP-065 con esta actualización.

## Protección de la demo en CI — 05/10/2026

Paris solicita un P2 sobre `b77d596` en
[Revision JUP-065](https://github.com/EconomiconFinOps/tfm-economicon/pull/63#pullrequestreview-5408829450):
los comandos de demo y el historial Git estaban presentes, pero los tests no
detectaban su pérdida. Se leyeron las siete reviews y ambas fuentes de
comentarios (conversación e inline vacías) antes de corregir.

`tools/ci-workflow.test.mjs` incorpora cuatro pruebas: una por cada comando
completo de demo en gobernanza y otra que exige `fetch-depth: 0` en su checkout.
Las líneas comentadas no satisfacen la comparación y los pasos de demo no
pueden tener `continue-on-error`. No se cambia el workflow ni el paquete.

Comprobado en Windows con Node 24.14.1 y Python 3.14.4:

- `corepack pnpm ci:check:test`: **14/14 PASS**.
- Seis mutaciones detectadas con salida 1: quitar cada comando por separado,
  quitar los tres juntos, quitar `fetch-depth` y cambiarlo a 1. El workflow se
  restaura byte a byte en `finally`; el control posterior vuelve a 14/14 PASS.
- Workflow, política PR, trazabilidad, higiene y gobernanza: **97/97 PASS**.
- Verificador normal y optimizado: **15/15 PASS**, sin regenerar originales;
  dos tests/cuatro controles negativos PASS; fuentes 28 consultas/siete categorías.
- OpenSpec **45/45**, diez changes trazables, higiene 842 archivos y
  `git diff origin/develop --check` PASS.

Logs y recibo de mutaciones en el espacio autorizado:
`materiales/07-evidencias/JUP-065-proteccion-ci-2026-10-05/` (fuera del repositorio).
Esta corrección requiere nueva revisión de Paris, con Approve para levantar su
Request changes, y revalidación de lo afectado por Víctor en el nuevo head.
La validación favorable de Víctor sobre `b77d596` permanece como evidencia de
esa combinación, no como aceptación automática del cambio posterior.
Pairing de Lucía sin acreditar; ensayo integrado `not_run`. No se ejecutó
runtime ni generación con modelo real en esta corrección; sin merge ni cierre.
Los cortes anteriores conservan sus resultados históricos.

## Nueva base con retrieval — 04/10/2026

Incorporado develop `c3aa9d68690ae718aecf1bee2f08cd25eb5f704f`, incluidas
#62/JUP-057, #60/JUP-061 y #67/JUP-022. GitHub `Update branch` devolvió 422
por conflicto en `.github/workflows/ci.yml`; resolución local conserva las
tres comprobaciones de demo y las tres de retrieval, historial completo del
job de gobernanza, `local:test` y el workflow separado `JUP reviews`.

El paquete `docs/demo/JUP-065/` y los quince originales no cambian frente a
`bf50073`; la referencia sigue fijada a `de0d62e`. Comprobaciones nuevas:

- Verificador normal y optimizado: 15/15 PASS antes de regenerar originales.
- Dos tests/cuatro controles negativos PASS; 28 consultas/siete categorías PASS.
- Gateway, topología, doctor/smoke, workflow y etiquetas retrieval: 140/140 PASS.
- Etiquetas retrieval: 28 coherentes (23 directas, tres parciales, dos sin cobertura).
- Calibración: 27 tests, 26 pasan y uno omitido por ausencia de
  `JUP086_VECTOR_TEST_URL`; no se ejecutó pgvector real.
- OpenSpec estricto 45/45, diez changes activos trazables, higiene 842 archivos
  y `git diff origin/develop --check` PASS. No se modifica whitespace heredado
  de la spec de anomalías de develop; el contraste se hace contra esa base.

Paris confirmó técnicamente `bf50073` y Víctor validó ese head
([review](https://github.com/EconomiconFinOps/tfm-economicon/pull/63#pullrequestreview-5403669755)),
incluido un recorrido local parcial de costes con mock. Son evidencias
históricas del head anterior. Esta combinación incorpora configuración,
embeddings y retrieval del backend, por lo que se solicita comprobación
incremental de Paris y Víctor antes de integrar. Una asociación automática de
reviews a un nuevo SHA no demuestra esa comprobación. El CI y el estado de
las aprobaciones del nuevo head se consultan en la PR.

No se arrancó un runtime ni un modelo en esta actualización. Con la nueva base,
el backend usa su propia clave de embeddings, modelo/dimensión compatibles e
índice reconstruido para el proveedor real; verificarlo en el ensayo conforme
a [ADR-0017](../adr/ADR-0017-backend-query-embedding-own-key.md) y al README del
backend. Integrar #67 no acredita chat con modelo real ni citas recuperables.
Se conserva el pending de pairing de Lucía o reasignación acordada y registrada.
Ensayo integrado `not_run`; sin merge ni cierre de JUP-065.

## Correcciones de revisión históricas — 03/10/2026

Paris solicitó dos P2 en `Revision JUP-065` sobre `e52853b` el 02/10.
Se leyeron esa review, la conversación y los comentarios inline antes de actuar
(no había comentarios adicionales). Proceso vigente: JUP-100, 2026-09-30.

- README ejecuta primero el verificador de originales, los controles negativos y
  el validador de fuentes. La regeneración opcional usa `--output` en otro destino.
  Se verificaron primero los quince originales; luego se probó la regeneración
  aparte. Los quince hashes originales permanecen idénticos.
- Se retira la obligación general de continuidad: AGENTS queda idéntico a develop.
  Los documentos técnicos de esta preparación se conservan; #64 no es dependencia.
- Incorporado develop `d6fc408b60e944b726605b242f3e7a64129282c7` por merge sin
  conflictos. `JUP reviews`, su workflow/política y `local:test` se preservan.
  La referencia de datos sigue en `de0d62e`; no se regeneraron los originales.
- Nueva reproducción normal y optimizada: PASS; dos tests/cuatro controles
  negativos PASS; fuentes copiadas 28 consultas/siete categorías PASS.
- Gobernanza y contratos de integración afectados: **198/198 PASS**, incluidos
  política de PR, workflow, reglas del repositorio, trazabilidad, higiene,
  herramientas local doctor/smoke y topología Docker. Los tests de herramientas
  no equivalen a arrancar el runtime.
- OpenSpec de la preparación archivado según CONTRIBUTING en
  `2026-10-03-jup-065-functional-demo`, con spec promovida. Los pendientes humanos
  y del ensayo se conservan explícitos en sus tareas y documentación.
- OpenSpec estricto **40/40 PASS**, ocho changes activos trazables; higiene y
  diff check correctos. El change JUP-065 se contrasta en el archivo y la spec
  promovida; el comando histórico `jup-check --change jup-065-functional-demo`
  ya no corresponde a un change activo.

Pendiente nueva aprobación de Paris que levante Request changes y review
`Validacion JUP-065` de Victor; pairing de Lucia sin acreditar. El nuevo CI se
consultará sobre el head publicado. El fallo de `JUP reviews` por pendientes
humanos no se elude ni se cuenta como check técnico aprobado.

## Resultados locales históricos — 01/10/2026

| Comprobación | Resultado nuevo |
| --- | --- |
| `python docs/demo/JUP-065/verificar.py --repo .` | PASS; quince archivos idénticos a la regeneración desde Git fijado |
| `python -O docs/demo/JUP-065/verificar.py --repo .` | PASS; guardas explícitas activas sin depender de assert |
| `python -m unittest discover -s docs/demo/JUP-065 -p 'test_*.py' -v` | 2 tests PASS, cuatro controles negativos: coste alterado, rúbrica inyectada, archivo faltante y archivo extra rechazados |
| `node docs/demo/JUP-065/generado/sources/tools/validation-questions.mjs validate` | 28 consultas, siete categorías y fuentes/rúbricas verificadas |
| `node tools/jup-check.mjs --change jup-065-functional-demo` | Trazabilidad PASS |
| `node tools/jup-cleanup-check.mjs` | Higiene PASS |
| `openspec validate --all --strict --no-interactive` | 36/36 PASS |
| Gobernanza: CI workflow, JUP check, higiene y política de PR | 32/32 tests PASS; nueve changes trazables |
| `git diff --check` | PASS |

Las pruebas negativas operan en copias temporales y no modifican la referencia
versionada. [Recibo de integridad](JUP-065-offline-results.json) conserva hashes.
Python estándar y Node; ninguna dependencia añadida al proyecto. CI obtiene
historial completo solo en gobernanza y ejecuta verificador, controles negativos
y validador de fuentes, conservando los siete contextos obligatorios.

## Referencias y limitaciones

La referencia se calcula independientemente con CSV y Decimal: 40 filas públicas,
38 registros recurso/grupo/día/moneda, ocho grupos (case-insensitive para resource
group) y coste 0,06 USD. La suma exacta CSV 0.060113199075769 no es una lectura
de CockroachDB. Se compara la salida de billing a dos decimales en el ensayo
posterior; no se afirma persistencia ni igualdad bit a bit del importe interno.
JUP-069-001 utiliza 1.000 EUR sintéticos suministrados como contexto separado.

**Runtime/LLM/ensayo integrado: not_run.** No se ejecutaron bases de datos,
proveedores externos, ingestas ni navegador. No se afirma calidad de respuestas,
despliegue, demo completa, ahorro obtenido ni cierre de tarjeta. La revisión de
Paris, validación de Victor y pairing de Lucia permanecen pendientes de evidencia
humana; el usuario autorizó publicar y solicitar, no aprobar en su nombre.

## Reproducción solicitada al validador

1. Obtener la rama y el SHA exacto publicado, con el commit de referencia disponible.
2. Ejecutar los comandos del README vigente desde la raíz, empezando por el verificador
   sin regenerar los ficheros: una regeneración previa podría ocultar una alteración.
3. Contrastar números, fechas, ausencia de filtración de rúbricas y casos límite.
4. Leer guion/preflight/plantilla y confirmar que límites y dependencias son claros.
5. Publicar resultado de preparación con SHA, comandos, incidencias y conclusión.
   No marcar como realizado el ensayo integrado ni cerrar JUP-065 por estas pruebas.
