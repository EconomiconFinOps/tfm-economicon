Revision JUP-131

**Veredicto del delta Azure: APPROVE.** No se encuentran P0/P1/P2 introducidos por los dos archivos revisados. No se encontró ningún consumidor del repositorio que dependa del hash o la inmutabilidad de instancias de esta clase `ApiError`.

Autor: agente independiente Codex `/root/pr161_code_review`, bajo la excepción autorizada el 24/10/2026. No representa a Lucía Mateo ni una review publicada en GitHub. Fecha: 24/10/2026, 23:35 Europe/Paris. PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/161.

La revisión inicial sobre base `ffb5d307772f697cffb8b1e73e6330250e093601` y candidato `e730dc15fb3feb45a3b346fc9e48332c4608b049` permanece intacta en [review.md](review.md). También se conserva el APPROVE del delta ALB en [revalidation.md](revalidation.md). HEAD sigue siendo `e730dc15fb3feb45a3b346fc9e48332c4608b049`, rama `feat/JUP-131-atlas-ecs`; este addendum revisa dos archivos locales adicionales, sin atribuirles un nuevo commit. Los cuatro archivos técnicos quedan cubiertos por ambos addenda, cada uno con sus hashes.

| Archivo Azure revisado | SHA256 de los bytes revisados |
| --- | --- |
| `apps/azure-cost-api/app/errors.py` | `389e2a7c72185d34122c89028c2147e64a0db904ac38190839e3b4844e4a4a48` |
| `apps/azure-cost-api/tests/test_errors.py` | `0cbc76998fdddd661c54c5d2bdc61542507ddcf992dbfebf582a2c0683886678` |

### Corrección y consumidores

En `errors.py:5-7`, quitar `frozen=True` elimina el `__setattr__` de dataclass que impedía asignar `__traceback__`. La clase sigue derivando de `Exception`, con los mismos cuatro campos y constructor. El log CI suministrado por el coordinador muestra el fallo al ejecutar `exc.__traceback__ = None` en Starlette; el nuevo test ejercita la restauración del traceback en `contextlib`, sin depender de una versión de Starlette. No se modifican las dependencias.

Se revisaron completamente `auth.py`, `scenarios.py`, `pagination.py`, `query_engine.py` y `main.py`, además de los dos archivos del delta, los requisitos y el contexto de pruebas. Los productores construyen y lanzan instancias nuevas. `main.py:77-83` registra el handler mediante la **clase**, y lee `status_code`, `code`, `message` y `headers` de la instancia para formar la respuesta. La búsqueda de referencias Python y consumidores versionados no encontró claves de diccionario, elementos de sets, cachés o comprobaciones de congelación basadas en instancias de `ApiError`. La caché de `config.py` corresponde a `get_settings()` sin argumentos. La clase TypeScript homónima del frontend es independiente.

El cambio sí elimina el hash generado por la dataclass congelada: las instancias nuevas son no hashables, incluso sin headers. Es un efecto real, comprobado, pero no rompe un consumidor identificado. Las instancias con headers de tipo dict ya podían fallar al calcular su hash antes del cambio. El registro de handlers usa el objeto clase y no resulta afectado. No se observan asignaciones de los consumidores a los campos de datos ni un uso de su congelación como garantía de seguridad.

El test nuevo conserva identidad de la excepción y comprueba status, código, mensaje y headers tras atravesar el gestor de contexto. Es una regresión acotada y falla por la causa observada, no por red o configuración de AWS. La respuesta HTTP sigue construyéndose con los mismos campos; la suite de integración ejecutada por el coordinador aporta la cobertura HTTP separada.

### Evidencia ejecutada por este revisor

- Lectura del diff y de todos los consumidores directos, búsqueda de usos de `ApiError`, hash, cachés y mutabilidad. `git diff --check` de los dos archivos: PASS.
- `python -B .work/pr161-code-review/azure_error_check.py`, Python 3.14.4: PASS. Carga la fuente original mediante `git show e730dc15fb3feb45a3b346fc9e48332c4608b049:apps/azure-cost-api/app/errors.py` y la fuente corregida en memoria. La primera produce `FrozenInstanceError` al restaurar el traceback; la segunda propaga la misma instancia. También comprueba asignar `None` y restaurar el traceback, igualdad de campos/args/payload y el cambio de hash descrito. No importa la aplicación ni carga `.env`.
- Evidencia propia reproducible: [azure_error_check.py](azure_error_check.py) y [azure-error-check.json](azure-error-check.json).

### Evidencia del coordinador y límites

Se leyeron el RED `.work/pr161-azure-fix/red.log` y los fragmentos pertinentes de `.work/pr161-metrics-fix/latest-ci-failed.log`: el run CI comunicado `40133534310` tiene 41 fallos/40 pases con la asignación de traceback como causa. Es una incompatibilidad preexistente expuesta por el stack permitido de dependencias; no se atribuye como un bug nuevo de la integración Atlas.

Se leyó el cierre de `.work/pr161-azure-fix/green-current-stack.log`: **82 PASS**, una advertencia de deprecación de `httpx` en TestClient. El coordinador informa FastAPI 0.162.0, Starlette 1.10.0, pytest 9.1.1 y Python 3.14.4 en un venv desechable. Este revisor no instaló ese entorno ni ejecutó esa suite; la evidencia se mantiene atribuida al coordinador. La nueva CI deberá confirmar Python 3.12.

No se ejecutaron suites amplias, servicios, HTTP, Terraform, Docker, AWS ni acciones cloud por este revisor. No se consumió el informe del validador. No se modificaron fuentes compartidas, documentación de proyecto, dependencias, commits o ramas. Este dictamen cubre sólo los bytes identificados; no acepta automáticamente cambios posteriores ni elimina los gates operativos descritos en los informes anteriores.
