# JUP-035: correccion SQL deadline local

Encargo autonomo12/10 07:42, diseño confirmado07:47, hostaddr confirmado07:57
Atlantic/Canary. HEAD954b44298ccd94994f3ac420a3aec55c32eeb521, worktree previo
conservado. REVIEW_FAIL P2 y guard independiente anterior intactos.

Solo chat_context.py/vector_store.py y tests existentes afectados, spec canonica
y continuidad. Sin nuevos servicios/dependencias, cambios TLS/tenant/filtros,
modelo/protocolo/budget, Git, builds, administracion o inferencia.

Conexion bounded request-owned con NullPool/async_creator: evita cola/pre_ping
del pool compartido; conserva SQL/REPEATABLE READ. Timeout restante de conexion,
statement_timeout/lock_timeout antes de ambas lecturas, supervision de cancelacion
y cierre antes de cancelar la coroutine para evitar fallback extra del driver.
Driver observado instalado: psycopg3.3.6/libpq180006, cancel_safe no bloqueante.
Direccion solo de driver ordinario ya autenticado; copia por peticion conserva
host/port/SSL/opciones. Sin peer o config inconsistente falla cerrado antes de DNS.
Sin fallback de una IP obsoleta; una conexion ordinaria posterior puede actualizar
la captura, nunca una consulta adicional creada por el chat para ese fin.

Expediente externo corrections/, prefijo requiredtool-dbdeadline-20261012-:
- design/hostaddr-design-spec.log: OpenSpec estricto exit0.
- red-worker.log: 4FAIL worker/query activo tras terminar coroutine, Red valido.
- green-worker.log: 4PASS; green-affected.log: 52PASS.
- hostaddr-red.log: 2FAIL por conexion sin hostaddr y ausencia no rechazada.
- hostaddr-green.log: 6PASS (conexion/SQL/documentos, timeout/cancel, TLS/peer).
- hostaddr-affected.log: 54PASS, warnings registrados; no sumar repeticiones.
- mutation.json: ignorar cancelacion/reintroducir lectura sincrona detectados.
- hostaddr-mutation.json: quitar hostaddr detectado, sin sintaxis/import errors.
- Guards separados design/red/green/mutation y hostaddr conformes.

Los tests usan doubles de driver/IO y greenlet_spawn real, sin DB. No acreditan
ack remoto del CancelRequest ni disponibilidad de IP obsoleta. En fallo de red,
statement_timeout es respaldo servidor; no se promete ack imposible. Falta
review independiente afectada y eventual edge PG real de parent, antes del caso
publico focal de recuperacion/citas/persistencia. No full28 ni JUP-070 formal.
Esquema/prompts/manifiesto y referencia de presupuesto anteriores intactos.
