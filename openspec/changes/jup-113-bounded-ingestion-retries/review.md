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

Tabla compartida `docs/api/ingest-source-contract-cases.json`: 16 aceptados y 19 rechazados, sin
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
