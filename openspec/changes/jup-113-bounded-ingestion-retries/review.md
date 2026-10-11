JUP: JUP-113
Trello: https://trello.com/c/JaHmg0fs

# Revisión JUP-113

Registro de evidencia por grupo de tareas, en orden de ejecución. Se completa con la revisión final
(tarea 8.4). Nada de lo que figura aquí se da por ejecutado si no consta su comando y su resultado.

Las pruebas de Python se ejecutan en este equipo con el entorno virtual local (Python 3.13.7), solo
sobre los archivos de cada tarea; la batería completa se ejecuta en un contenedor equivalente a CI
en la tarea 8.1, porque en Windows fallan pruebas ajenas del backend (`RF-105-004`).

## Grupo 1 — Reproducción y decisión

Mutación N/A — grupo sin código de producto (documentación, reproducción y ADR). Tester, coder y QA
no intervienen. Resultados en `docs/evidence/JUP-113-validation.md` y `docs/adr/ADR-0019-ingestion-retry-policy.md`.

## Grupo 2 — Regla de admisión del origen en el backend

### Red (tareas 2.2 y 2.4), 2026-10-11

Cifras históricas del commit Red (la tabla vigente tiene 16 aceptados y 20 rechazados, es decir 37 casos por
prueba, tras el caso de la sección «Mutación»). Tabla compartida `docs/api/ingest-source-contract-cases.json`:
16 aceptados y 19 rechazados, sin
desacuerdos con la regla del processor (comprobada con `strip().lower()` y `fullmatch`).

- `apps/backend/tests/test_ingest_source_admission.py` (nuevo, 36 casos):
  `cd apps/backend && python -m pytest tests/test_ingest_source_admission.py -q`.
  **Resultado Red: 17 fallan y 19 pasan.** Los 17 fallan por el motivo esperado,
  `assert 202 == 422`: la API admite el valor y crea el trabajo. Los fallos son `spaces-inside`,
  `two-words-lowercase`, `newline-inside`, `too-long-65`, `too-long-padded`, `leading-hyphen`,
  `leading-dot`, `leading-underscore`, `slash`, `colon`, `at-sign`, `comma`, `accented-letter`,
  `cyrillic-lookalike`, `zero-width-space`, `nul-character` y `dotted-capital-i`. Pasan `empty` y
  `whitespace-only` (ya se rechazaban), los 16 aceptados (hoy ya se admiten y se guardan literales) y
  el guardián de la tabla.
- `apps/processor/tests/test_ingest_source_contract.py` (nuevo, 36 casos):
  `cd apps/processor && python -m pytest tests/test_ingest_source_contract.py -q`. **36 pasan desde
  el principio**; describe comportamiento existente y por eso es una prueba de contrato y no un Red.
- Contraste: `tests/test_tenant_isolation_api.py` del backend, 16 pasan y 2 se omiten (variantes
  opt-in de CockroachDB), sin cambios.
- Los 36 casos se repitieron por separado por el orquestador con el mismo resultado. No hay cambios
  en `apps/*/app/**`.

Limitación declarada: en Red, las comprobaciones de que no hay efectos, de que la tabla `jobs` no
cambia y de que el valor no aparece en la respuesta ni en los registros solo se ejercitan de verdad
en los dos casos vacíos; en los otros 17 la aserción de estado falla antes. Quedarán probadas en
Green.

Hallazgos del tester a tener en cuenta en Green: la validación debe aplicar exactamente
`strip().lower()` de Python sobre `str` Unicode y `fullmatch` (no `$`, que acepta un salto de línea
final, ni `re.ASCII` ni `re.IGNORECASE`), porque `no-break-space-padding`,
`kelvin-sign-lowers-to-ascii` y `newline-inside` dependen de ello. Un NUL en una columna de texto de
PostgreSQL o CockroachDB podría dar un error de base de datos; con SQLite no, así que esa parte no
queda demostrada por esta prueba.

### Green (tarea 2.3), 2026-10-11

Producto modificado: solo `apps/backend/app/schemas/jobs.py`. `IngestJobRequest.validate_source`
aplica `SAFE_SOURCE.fullmatch(value.strip().lower())` y devuelve el valor original sin normalizar;
un único camino sustituye la comprobación de vacío. El patrón es una copia deliberada del de
`apps/processor/app/agents/guardrails.py`; la tabla compartida vigila que no diverjan.

- `test_ingest_source_admission.py`: **36 pasan, 0 fallan** (antes 17 fallaban con `assert 202 == 422`).
  Con el 422 ya existente se ejercitan de verdad las comprobaciones de no-efectos, de `jobs` sin
  cambios y de que el valor no aparece en la respuesta ni en los registros.
- Contraste, ejecutado por el coder y repetido por el orquestador: `test_tenant_isolation_api.py`,
  `test_job_publication.py`, `test_job_reservation_rejection.py`, `test_jobs_schema.py` y
  `test_ingest_tracing.py`, junto con la prueba nueva: 78 pasan y 4 se omiten (variantes opt-in).
  `test_ingest_padded_source_is_preserved` y `test_ingest_blank_source_is_rejected_without_effects`
  siguen pasando sin cambios.
- Processor, `test_ingest_source_contract.py`: 36 pasan (sin cambios de producto en el processor).
- Suite completa del backend en Windows, ejecutada por el coder: 1023 pasan, 64 se omiten y **145
  fallan**, todas en los cuatro archivos `*_jup047.py` de salud (`RF-105-004`, error
  `ProactorEventLoop ... _ssock`). El coder comprobó con el cambio retirado que dos de esos archivos
  fallan igual en la línea base (36 fallos); los otros dos no se ejecutaron en línea base. No se da
  por demostrado que los 145 sean preexistentes hasta la batería de la tarea 8.1 en contenedor Linux.
- Productores de `source` de `POST /jobs/ingest` revisados (`aws-cur`, `local-smoke`, `cd-smoke`,
  `assistant-corpus`, `test`, `azure-cost` y el caso con relleno ` azure `): ninguno es rechazado
  por la regla. La pantalla de ingesta envía el texto libre del usuario, así que un valor con
  espacios interiores pasa a recibir 422; lo que muestra la pantalla se comprueba en la tarea 6.4.
- Un comentario del coder decía que el processor «descartaría» ese trabajo; hoy lo reencola (es el
  defecto), así que el orquestador reformuló esa frase. Sin cambio de comportamiento.

### Mutación (tarea 2.5), 2026-10-11

Contenedor desechable `python:3.12` sobre una copia del árbol (el repositorio montado en solo
lectura), con `mutmut<3` (no corre en Windows y no se añade a ninguna dependencia del repo) acotado
a `app/schemas/jobs.py`, más 13 mutantes manuales dirigidos aplicados con una sustitución de texto y
la prueba `test_ingest_source_admission.py` como ejecutor. Línea base: 37 pasan.

Mutantes manuales: **12 muertos y 1 superviviente equivalente**.

| Mutante | Resultado |
| --- | --- |
| Sin `strip()`; sin `lower()` | muertos |
| Límite `{0,62}`; límite `{0,64}` | muertos |
| `match`; `search` en vez de `fullmatch` | muertos |
| Devolver el valor normalizado en vez del original | muerto |
| Primer carácter sin restringir; sin guion bajo; sin punto | muertos |
| Validación desactivada (`if False`) | muerto |
| `.casefold()` en vez de `.lower()` | **superviviente real en la primera pasada; muerto tras el caso `eszett-casefold-differs`** |
| El mensaje del `ValueError` incluye el valor | superviviente equivalente (ver abajo) |

Remediación (tester): se añadió a la tabla compartida el caso rechazado `eszett-casefold-differs`
(`straße`): `lower()` conserva la `ß`, que no es ASCII, y el patrón la rechaza; `casefold()` la
convertiría en `ss` y la aceptaría. Verificado por el tester contra el mutante (1 falla con
`assert 202 == 422`, 36 pasan) y contra el código real (37 pasan en backend y en processor), y
repetido por el orquestador en el contenedor (1 falla, 19 pasan por el corte del primer fallo).
Cambios de fichero: solo `docs/api/ingest-source-contract-cases.json`.

`mutmut` sobre el archivo: **6 supervivientes**, ninguno en código que cambia este grupo salvo los
dos equivalentes:

- Mutantes 1 y 2 (`strip_whitespace` y `min_length` de `NonEmptyText`) y 7 y 8 (valores por defecto
  de `artifact_uri` y `metadata`): líneas que este change no toca (`text_content`, `artifact_uri`,
  `metadata`). Fuera del alcance de la tarea; no se añaden pruebas para código ajeno.
- Mutante 11 (quitar `@classmethod` de `validate_source`): equivalente, `field_validator` de
  pydantic envuelve el método como método de clase por su cuenta.
- Mutante 13 y el mutante manual «mensaje con el valor»: equivalentes. `validation_error_handler`
  (`apps/backend/app/core/request_context.py`) descarta el `msg` de cada error y devuelve siempre
  `"Invalid request value"`, de modo que el texto del `ValueError` no es observable por la API. La
  garantía de no filtrar el valor la da ese manejador y la comprueba el test de no-eco ya existente.

Hallazgo de proceso: el fichero de casos, tal como se commiteó en el commit Red, contenía caracteres
no ASCII literales (incluido un espacio de ancho cero invisible) en lugar de escapes. Se convirtieron
a escapes `\uXXXX`; el contenido parseado es idéntico (comprobado por comparación) y no queda ningún
byte no ASCII. El cambio solo toca datos de prueba compartidos.

### Verificación del backend (tarea 2.6)

Suite completa del backend en contenedor `python:3.12` (equivalente a CI): **1169 pasan, 64 se
omiten, 0 fallan**, `compileall` correcto. Los 145 fallos de Windows son, por tanto, del entorno
(`RF-105-004`) y no del cambio: esos cuatro archivos pasan en Linux. Las 64 omitidas son las pruebas
opt-in con servicios reales; no se comparó el recuento con el de la base. `test_ingest_padded_source_is_preserved`
y `test_ingest_blank_source_is_rejected_without_effects` pasan sin cambios.

### DoD y QA del grupo 2

**DoD** (`node .claude/harness/check-dod.mjs`, Windows, 2026-10-11): lint, type-check y escaneo de
secretos **PASS**. La regresión completa queda **FAIL solo por el entorno**: el backend da 145
fallos, 1024 pasan y 64 se omiten, y los 145 están en los cuatro archivos `*_jup047.py` de
`RF-105-004` (72 + 37 + 33 + 3), cuyo recuento exacto ya consta en el backlog; turbo dio 3 de 4
paquetes correctos (azure-cost-api, frontend y processor). La misma suite del backend en contenedor
`python:3.12` pasa entera (1169 pasan, 64 se omiten, 0 fallan), así que el rojo no lo causa este
cambio. No se presenta el DoD como verde en Windows.

**QA (agente independiente): `accept-with-notes`.** Verificó con comandos propios: los tests no
cambian entre el commit Red y HEAD, el producto es solo `apps/backend/app/schemas/jobs.py`, los
cuatro escenarios de la spec tienen prueba (también la ausencia del valor en la respuesta y en los
registros), la tabla compartida coincide con la del commit Red salvo la entrada nueva y no tiene
bytes no ASCII, y los tres supervivientes justificados lo están (comprobó el manejador de
validación y el comportamiento de pydantic sin `@classmethod`). Sin hallazgos para tester o coder.
Limitación declarada por QA: no repitió la ejecución de `mutmut` en contenedor; se apoya en el
informe y en los datos que sí verificó. Notas: (1) cifras históricas de la sección Red, aclaradas
arriba; (2) los cambios sin commitear de la tabla, `review.md` y `tasks.md` entran en el commit de
cierre del grupo, porque las pruebas dependen de la tabla corregida.
