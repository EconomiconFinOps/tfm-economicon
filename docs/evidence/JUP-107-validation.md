# Evidencia de validación JUP-107

Tarjeta: [JUP-107](https://trello.com/c/ADFz3fpR). Change: `openspec/changes/archive/2026-10-08-jup-107-synthetic-cost-demo/` (tras archivarlo). Paquete: [`docs/demo/JUP-107/`](../demo/JUP-107/README.md).

Esta evidencia recoge lo que se ejecutó al implementar el change. **No es una validación independiente** (esa corresponde al rol de validación de la tarjeta) y **no es un ensayo con una persona presentando**: la ejecución de la receta es automatizada.

## Entorno

- Commit de la aplicación y del paquete de demo: `c1cc7bd` (rama `feat/JUP-107-synthetic-cost-demo`, sobre `develop` `2f9a5f5`).
- Stack Docker Compose aislado (`-p jup107`, volúmenes nuevos), Windows, Docker Desktop. Datos sintéticos cargados con `scripts/synthetic_costs.py` en `tenant-growth`.
- Receta de navegador: Node `v24.15.0`, `playwright-core` `1.63.0`, Chromium `153.0.8010.12` (revisión `1243`). Ejecución fuera del repositorio.

## Ejecución automatizada de la receta (modo: automatizada)

Fecha: 2026-10-08, sobre `c1cc7bd`. Resultado por paso (segundos medidos por la receta, no cronometraje de una persona):

| Paso | Resultado | s | Qué comprobó |
| --- | --- | --- | --- |
| D1 | pass | 2 | Core Finance activo y ningún importe en pantalla antes de la declaración |
| D2 | pass | 4 | Periodo «enero de 2026 – junio de 2026 (UTC)», totales EUR 90.00 (6) y USD 35.75 (2) |
| D3 | pass | 2 | Desglose por servicio, incluida la fila «Sin dimensión» |
| D4 | pass | 2 | Febrero 0.00 (1), marzo «—» y «Sin datos de esta moneda.», enero 100.00 (2), abril 40.00 (2); la curva del gráfico se interrumpe |
| D5 | pass | 2 | Mayo -50.00 (1); comparación mayo frente a enero, -150.00 EUR y -150.00 % |
| D6 | pass | 2 | Febrero 10.50 (1), junio 25.25 (1); comparación junio frente a febrero, +14.75 USD y +140.48 % |
| D7 | pass | 2 | Etiqueta `cost_center`: finance, ops y sin dimensión |
| D8 | pass | 2 | Aviso de 1 registro sin fecha excluido |
| D9 | pass | 3 | Core Finance sin datos y, al volver a Growth Ops, el periodo y los totales se conservan |
| D10 | pass | 2 | Paso hablado, sin comprobación de interfaz |
| D11 | pass | 5 | Opcional: aviso del límite de representación y 9007199254740993.01 (1) |

No se midió ni se afirma la duración de una presentación con una persona. Un ensayo humano solo existe cuando hay un registro relleno en `registro-ensayo.md`; no hay ninguno.

## Repetición de la receta contra la interfaz con la identidad de marca (modo: automatizada)

Fecha: 2026-10-12, sobre `9814e27` (la rama con `develop` al día, que ya incluye la identidad de marca de JUP-112 y los cambios de #114). La ejecución de 2026-10-08 se hizo antes de JUP-112; esta repetición comprueba que la demo sigue siendo válida con la interfaz nueva.

Stack aislado `docker compose -p jup107b` con volúmenes nuevos y la interfaz reconstruida desde esta rama, datos de JUP-106 cargados en `tenant-growth` (`present`, 2 ingestas y 10 registros), Playwright con Chromium revisión 1243, receta tal cual está en `receta-navegador.md`.

- **Resultado:** los 11 pasos (D1 a D11) `pass` con los `esperados.json` originales, sin cambiar la receta ni el paquete. Código de salida 0, dos veces seguidas (una antes y otra después de reiniciar CockroachDB, ver abajo).
- **Control positivo:** con una copia de `esperados.json` con el total de `F03` cambiado de 100.00 a 91.00, la receta sale con código 1 en D3 con `F03: falta la fila Compute EUR 91.00 (2)` y los pasos siguientes quedan `not_run`.
- Las capturas y el vídeo mudo se guardan fuera del repositorio.

Incidencias de la ejecución, ninguna del cambio:

- Hubo que descargar el binario de ffmpeg que pide la grabación de vídeo (`npx playwright-core install ffmpeg`), como cualquier persona que prepare la receta por primera vez.
- Mi primer control positivo falló por la razón equivocada: PowerShell 5.1 reescribió el JSON alterado con otra codificación y estropeó la raya larga del periodo, así que D2 falló por el texto y no por la cifra. No cuenta como control. El válido es el de arriba, hecho leyendo y escribiendo en UTF-8.
- CockroachDB del stack se paró una vez a mitad de trabajo con un error interno de su propio proceso (el mismo tipo que ya apareció arrancando bajo carga). Se reinició con `docker compose start`, los datos seguían y se repitió la ejecución completa.

No se midió ni se afirma la duración de una presentación con una persona; sigue sin haber ensayo humano.

## Controles positivos

La receta se ejecutó con `esperados.json` alterado y con entornos alterados; cada uno falla nombrando la causa y marca los pasos siguientes `not_run`:

- cifra de desglose `F03` alterada: `D3 fail: F03: falta la fila Compute EUR 100.01 (2)`;
- mes sin datos tratado como cero (`F11`): `D4 fail: F11: falta la fila mensual 2026-03 EUR 0.00`;
- porcentaje de la comparación en dólares alterado (`F17`): `D6 fail: F17: falta la variación porcentual +140.49`;
- una marca `no_amounts` puesta en un paso que muestra importes: `hay importes en pantalla antes de la declaración`;
- la comprobación del hueco aplicada a un mes sin curva: el paso falla;
- contraseña incorrecta: sale con código 2 y «No se pudo iniciar sesión».

## Comprobante por API

Con los datos cargados, el fragmento de `preparacion.md` imprime `data_status: partial`, `EUR 90.00 6` y `USD 35.75 2` para `tenant-growth` entre 2026-01-01 y 2026-07-01 (julio no entra), e imprime `data_status: empty` para `tenant-core`. Tras `remove`, imprime `data_status: empty` para `tenant-growth`.

## Estado inicial recuperado

`remove` repetido: `Retiradas 2 ingestas y 10 registros sinteticos.` y `Retiradas 0 ingestas y 0 registros sinteticos.`; `status` en `absent`; stack parado con `docker compose -p jup107 down -v` y sin volúmenes restantes. `apply` repetido informa `already-present` y no duplica nada.

## Pruebas y batería

| Comando | Resultado |
| --- | --- |
| `corepack pnpm synthetic-demo:test` | 40 pruebas correctas; también en `python:3.12-slim` sin paquetes |
| `corepack pnpm synthetic-costs:test` | 46 pruebas, 8 omitidas |
| `node --test tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 25 de 25 |
| `corepack pnpm openspec:validate` | 53 de 53 |
| `corepack pnpm jup:check:all`, `jup:cleanup:check` | correctos (913 archivos) |
| `git diff --check` | limpio |

## Hallazgos de la ejecución contra la interfaz real

- La pantalla arranca con los seis últimos meses completos según la fecha del día; el guion fija siempre el periodo.
- El total se muestra como «TOTAL EUR» (mayúsculas); la receta lo detectó al fallar el primer intento.
- El periodo se conserva al cambiar de cliente (comprobado). Por la lectura del código, el cliente activo se recupera del almacenamiento del navegador entre sesiones; no se comprobó en pantalla, pero la preparación pide abrir con Core Finance antes de D1 y la receta comprueba que lo está.
- Durante una ejecución la base de datos del stack aislado se paró por lentitud de disco (un fallo del entorno, no de la demo); se reinició con su volumen y los datos seguían cargados.

## No validado

- Cronometraje con una persona presentando y reproducción independiente de la demo por otra persona.
- La validación funcional de la tarjeta por quien tenga el rol de validación.
- El vídeo final, que no es parte de este change.
- La lógica de la receta no tiene pruebas automáticas propias (RF-107-001).
- Navegadores distintos de Chromium y pantallas móviles.

## Ampliación: datos sintéticos de anomalías (`jup-107-anomaly-demo-data`, 2026-10-11)

Segundo change de JUP-107, en la misma rama. Añade `scripts/synthetic_anomalies.py` (carga, estado y retirada), `docs/demo/JUP-107/esperados-anomalias.json`, `docs/demo/JUP-107/anomalias.md` y `scripts/call_anomalies_demo.py`, para enseñar las alertas de JUP-030 con dos periodos de siete días consecutivos en `tenant-core`. Son datos sintéticos: no son facturas de Azure ni vienen del dataset público.

### Pruebas

- `corepack pnpm synthetic-anomalies:test`: 30 pruebas, 24 sin base de datos y 6 con CockroachDB real (se omiten sin `JUP086_COCKROACH_TEST_URL`). Cubren: cada cifra del fichero de esperados frente a sumas exactas con `Decimal` y a las reglas reescritas desde el contrato; periodos consecutivos y de igual duración; fecha final no posterior al día UTC; idempotencia, negativa con datos ajenos, estado parcial y de otro tenant; retirada que solo toca lo suyo y es repetible; que cada herramienta ve las filas de la otra como ajenas; salida que declara el origen sintético en todos los comandos; códigos de salida 2 en las negativas; y la guía atada a los esperados (petición, script, tabla, primer párrafo, limitación del panel).
- Con CockroachDB real (`cockroachdb/cockroach:v24.1.11`, nodo desechable, migraciones del processor): 6 pruebas aprobadas. La CI **no** las ejecuta (no levanta CockroachDB): esta parte es manual y se ejecuta con `JUP086_COCKROACH_TEST_URL` apuntando a un nodo desechable.
- Mutantes: 12 sobre la herramienta (10 muertos sin base de datos; los 2 de SQL, `OR` en vez de `AND` en el borrado y marca sintética ignorada, mueren con la base real), y 22 más sobre guía, script, esperados y códigos de salida. Quedan 0 supervivientes. Como control negativo, quitar el paso de `ci.yml` hace fallar `tools/ci-workflow.test.mjs`.

### Contra el endpoint real

Stack aislado `docker compose -p jup107b` (todos los servicios sanos), `tenant-core` sin costes antes de cargar.

| Comprobación | Resultado |
| --- | --- |
| `status` previo, `apply` y `apply` repetido | `absent`; `loaded` con 1 ingesta y 22 registros; `already-present` |
| `POST /billing/anomalies/evaluate` con la petición de referencia, comparado automáticamente con el fichero de esperados | 0 diferencias en las siete evaluaciones; alertas `Analytics` y `Compute`; `evaluation_status` `provisional`; calidad `available` con 0 registros sin servicio en ambos periodos; `cause_status` `not_established` |
| Misma petición repetida | `id` y `evidence_id` idénticos |
| `deviation_threshold_percent` 4.55 y 4.54 sin umbral absoluto, con incremento mínimo 100.00 | 4.55: solo Compute; 4.54: Analytics y Compute (la comparación se hace antes de redondear) |
| Solo regla de subida con incremento mínimo 30.00 | Compute y Tools |
| `tenant-growth`, moneda `USD` | `unavailable` |
| Sin reglas, sin token, tenant ajeno | 422, 401, 403 |
| `/docs` y `/openapi.json` | 200, pero la cabecera `X-Tenant-Id` no está en OpenAPI: Swagger no sirve para esta ruta; la guía usa un script |
| JUP-106 cargado en `tenant-growth` | Esta herramienta lo ve como `other-tenant` con 2 ingestas y 10 registros reales y se niega a cargar ahí (salida 2); su `remove` deja el conjunto de JUP-106 intacto y `remove` repetido retira 0 |
| Ingesta del dataset público en `tenant-core` (38 filas) | `apply` se niega (salida 2) |
| La guía repetida paso a paso con los comandos tal cual | Funciona: `apply`, `status`, la llamada, `remove` repetido, `status` `absent` y 0 filas en `tenant-core` |

Nota: el script de la llamada se movió a `scripts/call_anomalies_demo.py` después de repetir la guía, porque `docs/demo/JUP-107/` solo admite `.md` y `.json`; su contenido no cambió salvo la ruta citada y no se volvió a ejecutar contra el stack.

Limpieza: `docker compose -p jup107b down -v` y borrado del nodo desechable; sin contenedores ni volúmenes restantes.

### Revisión adversarial

Primera pasada: `changes-requested`, con un BLOCKING (la salida de `apply` no declaraba el origen sintético, incumpliendo un SHALL), cuatro MEDIUM (guía no atada a los esperados, limitación del panel y declaración sin comprobar, códigos de salida sin probar, SQL no ejecutado por la CI) y tres LOW (orden de las alertas, `remove` con `--tenant` ignorado, periodo base ambiguo). Resueltos en `6e4afd1`; la segunda pasada dio `accept` y está en `review.md`.

### No validado

- Que una persona ensaye la guía y la cronometre.
- El panel `/anomalies`: sigue con datos de demostración y no lee el endpoint (cambio aparte con su propia tarjeta).
- La calidad de la detección con gasto real: los importes ilustran las reglas.
- El SQL de las pruebas con CockroachDB real en CI (manual).

## Nota de release

| Fecha | JUP | Nota de release | Review | ADRs |
| --- | --- | --- | --- | --- |
| 2026-10-08 | JUP-107 | Demo reproducible de la funcionalidad de costes con los datos sintéticos de JUP-106: guion de 3 minutos, preparación, preguntas, valores esperados verificados, receta de navegador y paso de CI `synthetic-demo:test`. | [review](../../openspec/changes/archive/2026-10-08-jup-107-synthetic-cost-demo/review.md) | Ninguno (no aplicable) |
