# JUP-029 — Evidencia del primer incremento

Fecha: 2026-10-01. [Trello](https://trello.com/c/pBICTDDh).
Base: `de0d62e` de develop. Rama: `feat/JUP-029-budget-thresholds`.

## Resultado funcional

Definicion y evaluacion de presupuesto por tenant/moneda/periodo explicito,
sin persistencia. [Contrato y ejemplo](../manuals/budget-evaluation.md).
Nuevo endpoint `POST /billing/budget/evaluate`; no requiere migracion.

Con B=100.00, S=80.00, devuelve consumo 80.00%, restante 20.00,
desviacion -20.00 y umbral 80.00 alcanzado. Con S=125.25 devuelve
restante -25.25, desviacion +25.25 y ambos umbrales alcanzados. Creditos y
consumo cero conservados. Ausencia de moneda => null/unavailable; parcial =>
provisional. 799.99/1000.00 no dispara el umbral 80 aunque redondee a 80.00%.

## Validacion local

Windows, Python 3.14, dependencias disponibles del entorno. Desde apps/backend:

- `python -m pytest tests/test_budget_evaluation.py -q`: 48 passed, 1 skipped.
  El omitido requiere Cockroach real; se ejecuta por separado mas abajo.
- `python -m pytest tests -q --disable-warnings`: 377 passed, 18 skipped,
  121.41 s. Skips de servicios externos opcionales. Avisos de deprecacion de
  dependencias/Python; no fallos. No se afirma ejecucion de todos los servicios.

Desde la raiz:

- `python -m compileall -q apps/backend/app`: correcto.
- `node tools/jup-check.mjs --change jup-029-budget-thresholds`: correcto.
- `node tools/jup-cleanup-check.mjs`: correcto.
- `openspec validate --all --strict --no-interactive`: 36 correctos, 0 fallos.
  Ejecutable 1.8.0 ya instalado en el checkout principal.
- `git diff --check`: correcto.

Los tests comprueban esquema (incluidos inputs numericos, NaN, fechas invalidas,
umbrales duplicados y campos de autoridad), aritmetica superior al limite exacto
de JavaScript, porcentajes no terminantes, redondeo HALF_UP, permiso/membresia
con identidades sinteticas reales y propagacion 409 sin importes.

## Cockroach real

Contenedor efimero exclusivo `jup029-budget-tests`, imagen
`cockroachdb/cockroach:v24.1.11`, almacenamiento en memoria, puerto remoto
`127.0.0.1:29229`, sin volumen persistente ni datos compartidos. Cluster marcado
`processor-integration-tests`; la fixture exige cluster vacio y crea/borra su
propia base con nombre aleatorio. El cliente Docker apunta a DockerServer.

Reproduccion: iniciar `start-single-node --insecure --store=type=mem,size=0.25
--cache=64MiB --max-sql-memory=64MiB` con ese puerto y establecer
`SET CLUSTER SETTING cluster.organization = 'processor-integration-tests'`.
Desde Windows usar tunel SSH `-L 127.0.0.1:29229:127.0.0.1:29229 DockerServer`.
Configurar `JUP086_COCKROACH_TEST_URL` con
`cockroachdb+psycopg://root@127.0.0.1:29229/defaultdb?sslmode=disable` y ejecutar:

```text
python -m pytest tests/test_budget_evaluation.py tests/test_billing_summary.py -q --disable-warnings --tb=short
```

Primer intento sin tunel: 56 passed, 8 errores de conexion; no se considero
evidencia funcional. Resultado con tunel: **64 passed, 0 skipped**, 82.14 s.
Contenedor efimero y tunel retirados al finalizar.

La referencia independiente incluye EUR=11.01 (cinco filas), GBP=0.00,
USD=9007199254740993.01, creditos, filas de otros tenants, fuentes en curso/fallidas,
fecha anterior y fin exclusivo. Para B=10.00 EUR el endpoint debe devolver
110.10%, desviacion 1.01/10.10%, restante -1.01 y estado provisional por una
fila sin fecha. Las pruebas JUP-026 verifican tambien solapamiento real.

## Limites y siguiente paso

### Revalidacion tras actualizar develop — 2026-10-02

Merge sin conflictos de `origin/develop` `11d63ea` en `5ee5862`;
incorpora JUP-099, JUP-096 y JUP-100. Sin cambios adicionales al producto JUP-029.
Repetidos sobre el merge los comandos anteriores: backend **377 passed,
18 skipped** (99.29 s); presupuesto y billing con Cockroach real **64 passed,
0 skipped** (69.92 s). Entorno aislado `jup029-revalidation-20261002`, mismo
puerto, imagen y tunel; retirado al terminar.

OpenSpec estricto **38/38**, `node --test tools/pr-policy.test.mjs` **57/57**;
trazabilidad JUP, higiene, compileall y diff check correctos. Avisos de
deprecacion de dependencias, sin fallos. La nueva CI se consulta en la PR.
El nuevo check `JUP reviews` exige las reviews tituladas `Revision JUP-029`
y `Validacion JUP-029`, todavia pendientes. Hacia develop la primera favorable
es Comment; la segunda aprueba cuando ambas estan satisfechas (JUP-100).

Esto no cierra la tarjeta padre: falta definir/implementar persistencia y el
flujo de usuario, y completar pairing, revision Paris y validacion Victor.
Estas pruebas automatizadas no sustituyen sus participaciones. No hay cambios
de frontend, notificaciones, motor forecast ni integracion del agente.


## Reconciliacion posterior a PR #61 — 2026-10-10

PR #61 fue integrada por Victorh1397 el 08/10/2026 a las 00:24:28 UTC en
`8cc5db0b8f96b7289f9b90dfed42527b76d0222d`. Esta entrega posterior incorpora
las dos regresiones propuestas por Victor: normalizacion del cero negativo y
maximos documentados/comparacion exacta con 26 digitos. El manual explica el
redondeo previo del total de billing v2. No cambia codigo de producto.

Las siguientes revisiones pertenecen a PR #61, no aprueban esta entrega:
- [Paris](https://github.com/EconomiconFinOps/tfm-economicon/pull/61#pullrequestreview-5408848343), sobre 0c9f6f0: 14 archivos, 12 enlaces y dos anclas, cuatro casos de configuracion y cuatro de calculo. Sin suite completa ni servicios reales.
- [Victor](https://github.com/EconomiconFinOps/tfm-economicon/pull/61#pullrequestreview-5407722492), sobre 0c9f6f0: backend estilo CI 626/29; presupuesto/billing 64/0 (8 Cockroach y 56 unitarios/SQLite); seleccion ampliada 250/0, adversarias 69 y 30 llamadas HTTP (corrige 31). Stack development/mock. Suite completa Cockroach sin conclusion por su entorno; managed_resolver no es hallazgo confirmado. Produccion/LiteLLM real no probados en Compose.

Las cifras historicas conservan fecha, SHA y autoria. La consulta del 10/10
no encontro nueva nota de conformidad de Lucia en Trello. El acuerdo operativo
06/10 admite aportaciones o visto bueno explicito mediante contraste asincrono,
registrado por la persona asignada en Trello; no exige sesion, commit coautor
ni repetir baterias. No se atribuye participacion no observada.

Pendientes: conformidad Lucia, archivo OpenSpec con actualizacion conjunta de
sus enlaces y reviews propias de esta entrega. Las tareas distinguen reviews
anteriores completadas del pairing pendiente. La tarjeta padre sigue abierta:
persistencia, UI, agente, forecast y notificaciones quedan fuera del incremento.
Las secciones anteriores son evidencia historica, no el estado actual.


### Comprobaciones de esta entrega posterior — 2026-10-10

Base: develop `412ae411c7f3a9b51f65407974962ac2b4545686`.
Ejecucion propia en Windows/Python 3.14 desde apps/backend:
`python -m pytest tests/test_budget_evaluation.py -q -x --tb=short`:
**50 passed, 1 skipped**, 13.04 s. Cockroach real no configurado; no se
certifican servicios reales ni suite backend completa. Las dos nuevas pruebas
estan incluidas en esas 50. Warnings de dependencias no auditados individualmente.
Primer intento desde raiz fallo por imports; desde backend el sandbox bloqueo
la preparacion de fixtures. Repeticion fuera del sandbox correcta, sin cambiar
producto para acomodar el entorno.

OpenSpec estricto 57/57, trazabilidad del cambio, higiene (1032 archivos) y
diff check correctos. El control de higiene tambien requirio ejecutar Git
fuera del sandbox (EPERM inicial). Sin nuevos mutantes propios; los ensayos
de mutacion de Victor se conservan como evidencia historica suya.
