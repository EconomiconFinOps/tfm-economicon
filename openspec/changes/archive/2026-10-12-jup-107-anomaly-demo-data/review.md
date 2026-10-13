# Review JUP-107 (ampliación) — Datos sintéticos de anomalías de coste

Fecha: 2026-10-11. Rama `feat/JUP-107-synthetic-cost-demo`, desde `develop` en `536fb4b`. Trello: https://trello.com/c/ADFz3fpR

## Resumen

Segundo change de JUP-107, en la misma rama que el primero (`jup-107-synthetic-cost-demo`, ya archivado). Añade `scripts/synthetic_anomalies.py` (`apply`, `status` y `remove`, con el patrón de `synthetic_costs.py` y prefijo propio), un conjunto de 22 registros sintéticos en euros con dos periodos de siete días consecutivos en `tenant-core`, el fichero de valores esperados `docs/demo/JUP-107/esperados-anomalias.json`, la guía `docs/demo/JUP-107/anomalias.md` y el script `scripts/call_anomalies_demo.py` que llama al endpoint de JUP-030. Con las reglas de referencia salen exactamente dos alertas (Compute por umbral y subida, Analytics solo por umbral) y cinco evaluaciones sin alerta, una por cada rama de la lógica. No cambia `apps/`: el panel `/anomalies` sigue con su fixture y su conexión es un cambio aparte.

## Decisiones

- Dos changes en una sola rama y un solo PR (decisión de Lucia del 2026-10-11): el primero se archivó tal cual con su aprobación del 2026-10-08 y este se prueba y se archiva después.
- Mismo código `JUP-107` para los dos changes (una tarjeta, dos carpetas); la ampliación excede la tarjeta tal como está escrita, que excluye modificar los datos de JUP-106 (aquí no se modifican, se añade un conjunto aparte). La tarjeta de Trello debería reflejarlo: lo decide y lo publica Lucia.
- Herramienta autocontenida y duplicada a propósito (se pasa por la entrada estándar y no puede importar otros módulos): no se toca `scripts/synthetic_costs.py`.
- Datos en `tenant-core` con prefijo `synthetic-jup107-`, para que cada herramienta vea las filas de la otra como ajenas.
- El script de la demo vive en `scripts/call_anomalies_demo.py` y no en `docs/demo/JUP-107/`: la primera parte vigila que ese paquete solo tenga `.md` y `.json` y sin asignaciones tipo `token:`.
- Excepción temporal del 2026-10-11: sin revisión ni validación humanas de otras personas en GitHub. Se sustituyen por la revisión adversarial independiente de este archivo, la evidencia de `docs/evidence/JUP-107-validation.md` y la aprobación de Lucia.
- ADR: no aplicable. Es un conjunto de datos de demostración y su documentación; no introduce una decisión de arquitectura duradera ni transversal.

## Validación

Comandos ejecutados el 2026-10-11:

| Comando | Resultado |
| --- | --- |
| `corepack pnpm synthetic-anomalies:test` | 30 pruebas: 24 aprobadas y 6 omitidas (las de CockroachDB real) |
| Las mismas 6 con `JUP086_COCKROACH_TEST_URL` apuntando a un nodo desechable (`cockroachdb/cockroach:v24.1.11`) | 6 aprobadas |
| `corepack pnpm synthetic-demo:test` y `corepack pnpm synthetic-costs:test` | 40 aprobadas; 46 aprobadas y 8 omitidas |
| `node --test tools/ci-workflow.test.mjs` | 12 aprobadas; con el paso quitado de `ci.yml` falla |
| `corepack pnpm openspec:validate`, `jup:check:all`, `jup:cleanup:check`, `git diff --check` | correctos (64 de 64) |
| Stack Docker aislado `jup107b`, carga, llamada al endpoint real, coexistencia con JUP-106, negativa con la ingesta pública y vuelta al estado inicial | 0 diferencias con el fichero de esperados; detalle en `docs/evidence/JUP-107-validation.md` |

Mutantes: 12 sobre la herramienta y 22 sobre guía, script, esperados y códigos de salida, todos muertos; los 2 de SQL solo los mata la base real, que la CI no ejecuta (`RF-107-002`).

## Adversarial Review (pass 1)

Veredicto: **changes-requested** (commit 938425c). 1 BLOCKING, 4 MEDIUM y 3 LOW.

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | BLOCKING | La salida de `apply` no declaraba el origen sintético, incumpliendo un SHALL de la spec | **Corregido**: `apply`, `status` y `remove` lo dicen; prueba que cubre todos los comandos |
| ADV-2 | MEDIUM | La petición de la guía, el script y la tabla no estaban atados al fichero de esperados | **Corregido**: pruebas que parsean el bloque JSON, el script y cada fila de la tabla |
| ADV-3 | MEDIUM | La limitación del panel y la declaración sintética no estaban comprobadas por la prueba | **Corregido**: exige la negación y la declaración en el primer párrafo |
| ADV-4 | MEDIUM | Los códigos de salida 2 de `apply` y `remove` rechazados no estaban probados | **Corregido**: pruebas de `main` con códigos y motivos |
| ADV-5 | MEDIUM | Nada en CI ejecuta la capa SQL | **Aceptado**: queda como manual en la evidencia y registrado como `RF-107-002`; se añadió la dirección inversa con SQL real |
| ADV-6 | LOW | El orden de las alertas del JSON y la guía era el contrario al del endpoint | **Corregido**: alfabético, atado por prueba |
| ADV-7 | LOW | `remove` aceptaba `--tenant` y lo ignoraba | **Corregido**: lo rechaza con salida 2 y la guía lo dice |
| ADV-8 | LOW | El periodo base se escribía «1 a 8» siendo el 8 exclusivo | **Corregido**: «del 1 al 7, ambos incluidos», derivado del fichero |

## Adversarial Review (pass 2)

Veredicto: **accept** (commit 6e4afd1). Los 8 hallazgos anteriores resueltos y sin BLOCKING ni HIGH. 1 MEDIUM y 3 LOW de robustez de las pruebas de la guía.

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-9 | MEDIUM | La prueba de la declaración aceptaba una frase negada | **Corregido**: exige la frase afirmativa exacta |
| ADV-10 | LOW | La celda «Diferencia» solo se comprobaba por prefijo | **Corregido**: igualdad exacta |
| ADV-11 | LOW | Cabecera y columna «Por qué» sin cubrir | **Corregido**: cabecera exacta, estados y mínimo atados |
| ADV-12 | LOW | «Dos alertas» y el orden no estaban atados al fichero | **Corregido**: derivados de `alerts` |

Observado y no cambiado: las salidas de error previas a tocar datos («Falta DATABASE_URL», tenant inválido, «No se pudo completar la operacion») no dicen «sintético»; no muestran filas y no se cambia.

Ataques que resistieron: fronteras de fecha (filas en el 1, 7, 8 y 14 de septiembre), el límite exacto de Analytics por multiplicación cruzada, `--tenant=...` y abreviaturas en `remove`, estados raros de `apply`, `status` y `remove` (parcial, otro tenant, filas reales mezcladas), script solo ASCII y autocontenido, control positivo contra el servicio real del backend (celda a celda con el fichero de esperados) y archivos protegidos sin cambios.

## Barrido de patrón

La aserción de mera presencia («esta cadena aparece») se encontró en cinco pruebas de la guía y se sustituyó por igualdad o por forma afirmativa. El patrón de salida sin «sintético» y de códigos de salida sin probar puede existir en la suite de `synthetic_costs.py`: no se revisó y queda como `RF-107-003`. El patrón de la capa SQL solo manual coincide con el de `synthetic_costs.py` (`RF-107-002`).

## Riesgos

- **Probados**: cifras frente al servicio real y frente a sumas exactas, límites de periodo, idempotencia, negativas, coexistencia con JUP-106 y con la ingesta pública, retirada repetible, guía repetida paso a paso, SQL real con 6 pruebas y 2 mutantes de SQL.
- **No comprobados**: un ensayo humano de la guía, que el reloj de quien ensaye sea posterior al 15/09/2026 (la prueba lo vigila), el script movido a `scripts/` contra el stack (se movió después de repetir la guía; el contenido no cambió salvo la ruta citada) y la ejecución de la capa SQL en CI.
- **Aceptados por Lucia (2026-10-11)**: `RF-107-002` y `RF-107-003`.

## Hallazgos registrados

`RF-107-002` y `RF-107-003` en `openspec/findings/backlog.md`, aceptados por Lucia el 2026-10-11.

## Human Approval

- Change: jup-107-anomaly-demo-data
- Approval type: post-review
- Decision: approved
- Approver: Lucia Mateo
- Date: 2026-10-11
- Archive decision: archive
- Scope reviewed: este `review.md` con las dos pasadas adversariales (la segunda en `accept`), la evidencia `docs/evidence/JUP-107-validation.md` (ampliacion), la herramienta `scripts/synthetic_anomalies.py`, el fichero de esperados, la guia `docs/demo/JUP-107/anomalias.md`, el script `scripts/call_anomalies_demo.py` y las pruebas. Lucia ejecuto ella misma la guia en PowerShell contra un stack aislado y vio la tabla esperada.
- Conditions approved: (1) `RF-107-002` y `RF-107-003` quedan registrados como hallazgos `Open`, aceptados y sin corregir en esta tarjeta. (2) El panel `/anomalies` sigue con datos de demostracion; su conexion es un cambio aparte. (3) La ampliacion se registra en la tarjeta de Trello cuando Lucia lo decida.
- Constraints: bajo la excepcion temporal del 2026-10-11 esta aprobacion sustituye la revision y la validacion de otras personas en GitHub, no las acredita, y no autoriza fusionar: el merge requiere orden expresa de Lucia. Aprueba los dos changes de JUP-107 (el primero ya estaba aprobado el 2026-10-08).
- Required changes before archive: ninguno.
- Notes: decision registrada a partir de la respuesta «si» de Lucia del 2026-10-11 a la pregunta de aprobar JUP-107 y aceptar `RF-107-002` y `RF-107-003`, dada tras su prueba manual de la guia.
