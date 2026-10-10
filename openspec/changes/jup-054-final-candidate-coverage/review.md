# Review — jup-054-final-candidate-coverage

JUP: JUP-054. Registro de evidencia por tarea durante el apply. El resultado global, la
checklist y el cierre se completan en la tarea 7.5.

## Excepción del ciclo Red/Green/mutación (grupos 1 a 4 y 5)

- **Grupos 1 a 4:** sin código de producto ni de pruebas (medición, auditoría y decisiones). Se
  omiten tester, coder y mutación, como en las tareas doc-only.
- **Grupo 5:** las pruebas se escriben sobre código de producto que ya existe, por lo que pasan a
  la primera y no hay Red en sentido estricto. El Red se sustituye por la rotura manual del
  comportamiento cubierto (decisión 7 del `design.md`), hecha **sólo en una copia desechable dentro
  de un contenedor**, nunca en el árbol de trabajo. El `coder` no interviene: no hay cambio de
  producto. Si una prueba fallara contra el candidato sin modificar, se registra un hallazgo (5.10).
- **Mutación automática (Stryker/mutmut):** no se ejecuta; la sustituyen las roturas manuales
  (decisión 7). Los mutantes supervivientes de cada tarea se listan con su justificación.
- **Entorno de ejecución:** contenedores Linux con Python 3.12 y las dependencias de
  `requirements-dev.txt`, equivalentes a CI. El backend en Windows tiene fallos conocidos de
  `socketpair` (evidencia de la primera pasada), así que no se usa para esta verificación.

## Tarea 5.1 — H-02, `GET /tenants` (backend)

- **Archivo nuevo:** `apps/backend/tests/test_tenants_route.py`, 10 pruebas, SQLite real y
  autenticación real; sin skips ni xfail.
- **Comando:** `python -m pytest tests/test_tenants_route.py -q -p no:cacheprovider` desde
  `apps/backend` (Python 3.12).
- **Resultado limpio:** 10 passed. Junto a `test_tenant_isolation_api.py`, `test_cors.py` y
  `test_auth_api.py`: 162 passed y 2 omitidas (opt-in CockroachDB preexistentes), sin interferencias.
- **Roturas del tester** (en copia desechable): `fetch_tenants` sin filtro por usuario (4 fallan),
  ruta sin `get_current_user` (9 fallan), rol admin recibe todos los tenants (1 falla) y usuario
  inexistente aceptado (1 falla). Cada una falla por el motivo esperado.
- **Roturas independientes de QA:** orden invertido, filas duplicadas, JOIN que multiplica filas,
  filtro de usuario debilitado con `OR ut.role='member'`, resultado truncado, `plan` nulo, tenant
  leído de `X-Tenant-Id` y usuario inexistente aceptado. Las ocho se detectan.
- **Mutante superviviente (justificado):** eliminar por completo la cláusula `ORDER BY t.name` de
  `fetch_tenants` no hace fallar ninguna prueba. SQLite devuelve las filas en su orden natural, que
  coincide con el alfabético, y el fixture compartido tiene `id == name`, de modo que el orden por
  `id` o por `name` es indistinguible. La prueba detecta un orden alterado o invertido, no la
  ausencia de orden. Distinguirlo exige datos distintos en un fixture compartido, fuera del alcance
  de este hueco; el orden no está garantizado por el contrato fuera de SQLite.
- **Veredicto QA:** accept. Sin hallazgos bloqueantes. No hay caso de membresía revocada porque
  con el esquema actual equivale a no tener fila en `user_tenants`, ya cubierto por `admin-alone` y
  por la ausencia de tenants ajenos.
- **Producto:** sin cambios (`git diff --stat -- apps` vacío; sólo el archivo nuevo).

## Tarea 5.2 — H-03, `POST /assistant/conversations` con éxito (backend)

- **Archivo nuevo:** `apps/backend/tests/test_conversation_creation.py`, 26 casos con SQLite real,
  autenticación real y validación de pertenencia real; sin skips ni xfail. No repite los casos de
  `test_tenant_isolation_api.py` (422 por `user_id` en el cuerpo y 404 indistinguible de ids ajenos).
- **Comando:** `python -m pytest tests/test_conversation_creation.py -q -p no:cacheprovider -W ignore`
  desde `apps/backend` (Python 3.12).
- **Resultado limpio:** 26 passed. Con `test_tenants_route.py`, `test_tenant_isolation_api.py` y
  `test_assistant_service.py`: 54 passed y 2 omitidas (opt-in CockroachDB preexistentes). QA repitió el
  archivo tres veces seguidas, en orden inverso y duplicado en la misma invocación: 26 passed siempre.
- **Qué cubre:** respuesta 201 con la forma exacta del registro, id uuid4 por patrón, tenant y usuario
  tomados del contexto autenticado (cuatro identidades y un usuario multi-tenant en ambos tenants),
  título recortado, `created_at == updated_at`, fila persistida idéntica a lo devuelto, una sola fila
  nueva sin tocar las existentes ni `messages`, ids distintos en creaciones consecutivas, lectura por su
  dueño, invisibilidad para otro tenant, otro usuario y el mismo usuario en otro tenant, presencia sólo
  en el listado de su dueño y tenant, y rechazos sin escritura (401 sin token y con token inválido, 400
  sin `X-Tenant-Id`, 403 sin pertenencia incluido un admin sin membresías, 422 con título vacío o ausente).
- **Roturas del tester** (copia desechable): título fijo o sin recortar (también vía esquema), `user_id` y
  `tenant_id` fijos en la inserción, ruta sin autenticación, `get_active_tenant` sin pertenencia,
  `fetch_conversation(es)` sin filtro de usuario o de tenant, `updated_at` distinto, INSERT omitido con
  registro devuelto e `id` fijo. Todas detectadas. Una (listado sin filtro de tenant) sobrevivió a la primera
  versión del archivo y se mató añadiendo el caso del usuario multi-tenant.
- **Roturas independientes de QA** (siete): fechas fijas en el año 2000, 200 en lugar de 201, una fila extra
  en `messages`, título persistido distinto del devuelto, campo extra en el registro, detalle sin filtro de
  usuario con 404 de cuerpo distinto, y `uuid1` en lugar de `uuid4`. Las siete se detectan.
- **Matiz de la rotura «ruta sin autenticación»:** quitar `get_current_user` sólo de la ruta no se observa
  como 401 porque `get_active_tenant` depende de él; por eso se rompió también `get_current_user`, y eso sí
  se detecta.
- **Riesgo de reloj, valorado por QA:** la ventana `antes <= created_at <= despues` usa el mismo reloj, en el
  mismo proceso, que el producto, sin red de por medio, así que la deriva entre host y contenedor de
  `RF-085-002` no le afecta. Sólo fallaría con un retroceso del reloj durante los milisegundos de la
  llamada. Se acepta sin tolerancia añadida.
- **Límite conocido:** `get_active_tenant` también responde 400 con cabecera `X-Tenant-Id` duplicada, con
  espacios o con comas; aquí sólo se prueba la cabecera ausente. Es una dependencia compartida por todas
  las rutas y queda fuera de este hueco.
- **Sin supervivientes.** Veredicto QA: accept. Producto sin cambios (`git diff --stat -- apps` vacío).
