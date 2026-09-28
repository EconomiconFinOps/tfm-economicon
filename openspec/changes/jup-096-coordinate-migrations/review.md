# Review JUP-096

JUP: JUP-096

## Resumen

Cierra RF-044-002: backend y processor ya no crean ningun objeto de esquema en comun, de modo que migrar a la vez una base vacia no puede fallar, y el processor arranca en Docker Compose solo cuando el backend esta sano. La revision adversarial añadio tres mejoras sobre el mismo alcance: `/health` del processor tolera la ausencia de `jobs` sin ocultar otros errores, una guarda estatica en CI vigila la propiedad de las tablas y el runner del processor exige su tabla de versiones.

## Decisiones

Ver [design.md](design.md): dueño unico de `jobs` en el backend editando la `001` del processor (1), dependencia `processor` -> `backend` sano (2), sin reintentos ni lock (3), `/health` degradado solo si falta `jobs` (4) y sin ADR nuevo (5).

## Validacion

Detalle y comandos en [docs/evidence/JUP-096-validation.md](../../../docs/evidence/JUP-096-validation.md).

- Exploracion en `develop`: carrera 7/7, control sin `jobs` 0/6, Compose real 0/5 (proteccion accidental por ~90 s de desfase).
- RED: 3 fallos en los tests opt-in con CockroachDB real; el test de topologia falla con el compose de `develop`.
- GREEN: opt-in 40/40, backend 259, processor 361 (+40 opt-in saltados), topologia 28/28.
- Controles positivos: la `001` antigua vuelve a romper los tests opt-in y la guarda estatica.
- Docker real: 3 arranques en frio sanos, orden medido con `docker events` y camino de error con el backend sin sanar; repetido tras los cambios de `/health` y del runner (backend arranca 23:17:44, processor 23:18:25, ambos sanos, `/health` del processor `ok` con cuentas).

## Adversarial Review

Agente `adversarial-reviewer` con solo spec, proposal, design y diff. Diez pasadas; desde la 5 los hallazgos se concentran en la guarda estatica, que es heuristica por naturaleza (su limite queda en RF-096-004).

### Pass 1 - accept

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-1 | MEDIUM | `/health` del processor respondia 500 (`UndefinedTable jobs`) si el backend no habia migrado; regresion frente a `develop` | Corregido con RED/GREEN y requisito nuevo en la spec |
| ADV-2 | MEDIUM | Ninguna guarda en CI contra volver a duplicar DDL (los opt-in se saltan) | Corregido: guarda estatica |
| ADV-3 | MEDIUM | El backend lee tablas pgvector que crea solo el processor; `send_message` da 500 y deja un mensaje huerfano | Registrado RF-096-002; riesgo aceptado por Lucia |
| ADV-4 | LOW | El test de concurrencia no verificaba la simultaneidad ni la definicion de `jobs` | Corregido: barrera comprobada y columnas de `jobs` |
| ADV-5 | LOW | Dos procesos del processor migrando a la vez fallan 5/5 | Registrado RF-096-003 por decision de Lucia |

### Pass 2 - accept

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-6 | MEDIUM | El `except Exception` de `/health` ocultaba cualquier error y convertia una BD caida en 200 | Corregido: solo degrada si falta `jobs`, con aviso en log |
| ADV-7 | MEDIUM | El escaner no veia DDL habitual (esquema, comillas, indices, `RENAME`, `TRUNCATE`) | Corregido: 14/14 casos hostiles |
| ADV-8 | LOW | RF-096-003 citaba solo la 003 como no transaccional | Corregido: 003 y 004 |
| ADV-9 | LOW | RF-096-002 afirmaba que la ventana no crecia | Corregido con medidas (puede crecer 5-25 s); Lucia reconfirmo la aceptacion |
| ADV-10 | LOW | `MigrationRunner` del processor usaba por defecto la tabla de versiones del backend | Corregido: parametro obligatorio |

### Pass 3 - accept

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-11 | MEDIUM | El escaner capturaba nombres falsos y dejaba escapar `ONLY`, `TEMP`, listas y SQL construido a trozos | Corregido: lista blanca por servicio, 26/26 casos |
| ADV-12 | LOW | `has_table` resolvia `jobs` de forma distinta a la consulta real | Corregido: se cuenta primero y la existencia solo se comprueba ante un error de BD |
| ADV-13 | LOW | `has_table` duplicaba la latencia de `/health` | Corregido con el mismo cambio |
| ADV-14 | LOW | `design.md` y `proposal.md` no reflejaban el nuevo `/health` | Corregido |
| ADV-15 | LOW | Diagnostico `backend_schema_missing` con `jobs` en otro esquema o `"Jobs"` | Aceptado por Lucia sin cambios |

### Pass 4 - accept

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-16 | MEDIUM | DDL sin nombre capturable (`DROP INDEX idx`, `create_all`, DDL importado, `.sql`) pasaba el escaner | Parcial: formas sin tabla prohibidas y cada migracion declara tablas o esta marcada sin DDL; el resto aceptado por Lucia como limite de una guarda heuristica y RF-096-004 registrado |
| ADV-17 | LOW | Falsos positivos por comentarios, `RENAME TO` de indices y `GRANT` multilinea | Corregido; los literales se mantienen a proposito (fallo seguro) |
| ADV-18 | LOW | 500 aislado si el backend crea `jobs` entre las dos comprobaciones | Aceptado por Lucia |
| ADV-19 | LOW | `tasks.md` e Impact no recogian todo el alcance | Corregido |

### Pass 5 - accept

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-20 | MEDIUM | Quitar comentarios `#`/`--` del texto fuente borraba DDL dentro de strings (regresion introducida al corregir ADV-17) | Corregido: el escaner analiza los strings con `ast` y solo quita comentarios SQL respetando los literales |
| ADV-21 | MEDIUM | `"...;
ALTER TABLE jobs"` en un string de una linea no se detectaba | Corregido con el mismo cambio (los escapes llegan decodificados) |
| ADV-22 | LOW | RF-096-004 citaba tests del PR #47, rangos de tiempo distintos y What Changes incompleto | Corregido |

### Pass 6 - changes-requested

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-23 | MEDIUM | Con `ast`, nombres añadidos con `+` tras `TRUNCATE`, listas, `RENAME TO`, `STATISTICS ... FROM` o `GRANT ... ON` ya no se detectaban | Corregido: todo literal que continua en codigo se analiza como si le siguiera un nombre desconocido |
| ADV-24 | LOW | Literales `bytes` ignorados | Corregido |
| ADV-25 | LOW | Falsos positivos en docstrings y trozos de f-string | Corregido |

### Pass 7 - changes-requested

Comparacion automatica de 1.710 entradas contra las versiones anteriores del escaner.

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-26 | MEDIUM | La regla del nombre desconocido solo se aplicaba si el literal acababa en espacio o coma (`" ".join`, `format`, `%` y espacios Unicode escapaban) | Corregido: se aplica a todo literal |
| ADV-27 | LOW | `COMMENT ON COLUMN` sin punto lanzaba `IndexError` | Corregido |
| ADV-28 | LOW | `DROP/ALTER INDEX IF EXISTS tabla@idx` se prohibia por error | Corregido |
| ADV-29 | LOW | `--` dentro de identificadores entre comillas dobles o `$$` | Documentado como limite en RF-096-004 |

### Pass 8 - changes-requested

Comparacion de 2.202 fuentes contra cuatro versiones.

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-30 | MEDIUM | La correccion de ADV-28 dejaba pasar `DROP/ALTER INDEX IF EXISTS` con nombre construido por codigo | Corregido |
| ADV-31 | MEDIUM | `_forbidden` no aplicaba la continuacion de literales | Corregido con una normalizacion compartida |
| ADV-32 | LOW | Falsos positivos ruidosos con texto en ingles acabado en palabras DDL (`"cannot alter table"`) | Sin cambios: falla de forma visible; aceptado por Lucia |
| ADV-33 | LOW | Cadenas `e'...'` | Documentado en RF-096-004 junto a ADV-29 |

### Pass 9 - accept

Comparacion de 1.890 casos contra cuatro versiones: cero falsos negativos nuevos.

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-34 | LOW | `DROP INDEX CONCURRENTLY tabla@idx` se prohibia por error | Corregido tras la pasada, con casos que mantienen prohibidas las variantes sin tabla |

### Pass 10 - accept

Acotada al commit de ADV-34; comparacion de 42.000 fuentes de `DROP/ALTER INDEX`.

| ID | Sev. | Hallazgo | Tratamiento |
|---|---|---|---|
| ADV-35 | LOW | Un indice sin comillas llamado literalmente `concurrently` (o `if`, ya antes) escapa a la prohibicion de indices sin tabla | Documentado como limite en RF-096-004; aceptado por Lucia |

Veredicto final: **accept** (pasada 10). Sin findings BLOCKING, HIGH ni MEDIUM abiertos.

## Barrido del patron

- DDL duplicada entre servicios: ninguna tras el cambio (guarda estatica y tests opt-in).
- Un servicio leyendo tablas de otro sin orden garantizado: `jobs` desde el processor (cubierto por el orden de Compose y `/health` degradado) y tablas pgvector desde el backend (RF-096-002).
- Migraciones sin coordinacion entre procesos del mismo servicio: RF-096-003.
- Tests con servicios reales saltados en CI: RF-096-004 (tambien observado en la revision del PR #47).

## Riesgos aceptados por Lucia

- ADV-3 / RF-096-002 (27/09/2026): "si"; reconfirmado tras corregir la estimacion de la ventana: "confirmo".
- ADV-5 / RF-096-003 (27/09/2026): "registramos".
- ADV-15, resto de ADV-16 y ADV-18 (28/09/2026): "si".
- ADV-32 (falsos positivos ruidosos de la guarda estatica, incluidos espacios dobles antes del nombre del indice) y ADV-35 (28/09/2026): "apruebo".

## Findings

- RF-044-002: `Fixed (local, sin integrar)`.
- Nuevos: RF-096-001 (RabbitMQ `eacces` intermitente), RF-096-002, RF-096-003 y RF-096-004.

## ADR

No aplica ADR nuevo: la regla duradera queda como requisito verificable en la capacidad `schema-migration-ownership` (design, decision 5).

## Human Approval

- Change: jup-096-coordinate-migrations
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-09-28
- Adversarial review: accept (pass 10) | accepted findings: ADV-3 (RF-096-002), ADV-5 (RF-096-003), ADV-15, resto de ADV-16 (RF-096-004), ADV-18, ADV-32, ADV-35
- Archive decision: archive
- Notes: revisados codigo, specs, diseño, evidencia y revision adversarial. Pendiente en Trello: revision del PR (Victor Mendez) y validacion funcional (Paris Arcos Martin).
