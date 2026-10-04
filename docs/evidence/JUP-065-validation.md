# JUP-065 — Validación de la preparación de demo

Fecha: 2026-10-01. [Trello](https://trello.com/c/SZUFo4ol).
PR [#63](https://github.com/EconomiconFinOps/tfm-economicon/pull/63).
Rama: `docs/JUP-065-functional-demo`, sobre develop
`de0d62e7c0028f35a81c5087f531d19031a90e81`.
[Paquete](../demo/JUP-065/README.md) y
[alcance OpenSpec](../../openspec/changes/archive/2026-10-03-jup-065-functional-demo/proposal.md).

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
