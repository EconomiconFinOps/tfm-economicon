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
