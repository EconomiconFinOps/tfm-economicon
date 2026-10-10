# JUP-027 — Evidencia de showback

Verificado el 2026-10-10. [Tarjeta](https://trello.com/c/W6gAiOWt). Base de implementación: develop `c2995a1`. Esta es evidencia técnica del candidato, no una `Validacion JUP-027` independiente.

## Criterios de la tarjeta

| Criterio | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | GET /billing/showback implementado con cuatro dimensiones, tenant autenticado, reparto directo, importes sin asignar, monedas separadas y reconciliación exacta. [Contrato y uso](../api/showback.md). HTTP y SQL real aprobados, incluida atribución a equipo/aplicación desde el endpoint. |
| Pruebas necesarias añadidas y en verde | 80 casos aprobados: 48 de servicio, 23 HTTP y 9 SQL real. La última ejecución SQL terminó con 9 passed en 80,08 s; sin omisiones. |
| Documentación y decisiones actualizadas | Contrato API, diseño y escenarios [OpenSpec](../../openspec/changes/jup-027-organizational-showback/proposal.md), [continuidad](../continuidad/showback-unidad.md). OpenSpec estricto: 56/56. |
| Pull request revisado y vinculado | [PR #101](https://github.com/EconomiconFinOps/tfm-economicon/pull/101) draft hacia develop, código probado `699a9b3`. Revisión independiente pendiente de regularización de roles; la comprobación automatizada no la sustituye. |
| Validación funcional y evidencia enlazadas | Evidencia enlazada desde Trello, comentario `6ac9ed3da7b90649326c2076`, publicado por la integración oficial y verificado en la respuesta. `Validacion JUP-027` de Lucia pendiente. No se afirma aceptación humana. |

## Entorno y reproducción

Windows; Python 3.14.4, pytest 9.0.3, FastAPI 0.115.12, Pydantic 2.12.5, SQLAlchemy 2.0.52, psycopg 3.2.13. Node 24.14.1, pnpm 9.0.0, OpenSpec 1.8.0. CockroachDB `cockroachdb/cockroach:v24.1.11` en DockerServer, contenedor temporal sin volumen, puerto SQL exclusivo loopback 36427, organización de prueba `processor-integration-tests`. Acceso desde Windows por `ssh -N -L 127.0.0.1:36427:127.0.0.1:36427 DockerServer`. Datos y usuarios sintéticos; no se usa ni modifica una base de aplicación.

Desde `apps/backend`, con las dependencias de `requirements-dev.txt` instaladas:

```powershell
$env:JUP086_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:36427/defaultdb?sslmode=disable'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
python -B -m pytest -p no:cacheprovider tests/test_showback_service.py tests/test_showback_api.py tests/test_showback_repository.py -q --basetemp=<directorio-temporal-exclusivo>
```

La fixture SQL exige una instancia nueva, marcada y sin bases de usuario; crea una base aleatoria, aplica migraciones reales de backend/processor y elimina únicamente la base creada. Sin la variable de conexión los nueve casos SQL se omiten; una omisión no acredita integración. El primer intento SQL falló por timeout: el contexto Docker default era remoto y aún faltaba el túnel. No fue un resultado funcional del SQL.

La suite pura pasó con `--noconftest` para evitar la fixture global de temporales, tras `WinError 5` en el ejecutor Windows. Esa suite no depende de configuración, red ni base de datos. No se modificaron sus aserciones.

La ejecución conjunta conservó todas las fixtures y obtuvo 71 aprobadas antes del timeout de conexión SQL. Tras abrir el túnel se ejecutó `tests/test_showback_repository.py`: 9 passed, 0 skipped. Se usó un ejecutor local que cambia únicamente `pathlib.Path.mkdir(mode=0o700)` a `mode=0o777` para heredar la ACL del directorio de pruebas sintéticas en este entorno Windows. Se mantuvieron intactos código, datos y aserciones; se desactivó el autoload de plugins externos. En un entorno sin esa incidencia se usa el comando estándar anterior.

Otros controles: instalación `pnpm install --frozen-lockfile --offline --ignore-scripts` correcta, sin cambio de lockfile; 82 pruebas de política PR, gobernanza y workflow CI aprobadas; `jup:check:all`, `jup:cleanup:check`, `git diff --check` y compilación de backend correctos. OpenSpec estricto: 56/56. El primer intento Node encontró `spawn EPERM` del sandbox y luego faltaba `yaml` en la copia nueva; ambos resueltos con ejecución autorizada e instalación bloqueada desde caché.

## Alcance de las comprobaciones

- Servicio: cuatro dimensiones, trim y sensibilidad de identificadores, missing/invalid, créditos, cero/vacío, monedas, cantidades superiores a 28 dígitos, cancelación y contexto Decimal externo de baja precisión.
- HTTP: tokens y pertenencia reales sobre identidades SQLite; doble explícito únicamente del repositorio de costes. Períodos, fechas, dimensiones, suplantación de tenant en query, dinero textual y 409 sin filtraciones.
- SQL: consulta real sobre Cockroach y fixture independiente del normalizador. Límites de período, tenant/run/subscription adulterados, estados running/failed, solapamiento, project tipado/fallback, valores JSON no textuales y reconciliación.
- Revisión estática automatizada adicional sin hallazgos materiales. No se publicó una review en nombre de los roles humanos.

## Dependencias y límites

JUP-015 sigue sin integrarse en la base de esta rama. Se ha contrastado su candidato de contrato `docs/finops/tagging-taxonomy.json`, SHA-256 `7107e65b5c6e2812dcf53df8eb67ebbe567f4cf132d31c4b6673e67c327518c3`: mismas claves, expresión de identificadores y marcadores de `economicon-minimum-v1`. Showback usa un adaptador provisional aislado y no certifica catálogos corporativos, jerarquías ni `owner_to_org_unit`.

La cuenta de entrega es `Iber1to` (Alejandro, según el registro del repositorio), mientras que Trello asigna liderazgo a Paris y revisión a Alejandro. Esta entrega es una contribución propia para Paris: no se reasignan roles por inferencia y Alejandro no puede firmar una revisión independiente de su propia contribución. Antes de promover el draft, el equipo debe regularizar autoría/participación y una revisión independiente conforme a CONTRIBUTING, dejando constancia en Trello y PR.

No probado: Azure vivo, datos reales de cliente, carga/rendimiento, UI, despliegue, chargeback, reglas porcentuales de gasto compartido o consumo por otro servicio. No se modifica JUP-028. No se atribuyen pairing Victor, revisión Alejandro, validación Lucia ni aceptación Paris sin evidencia. La tarjeta no puede darse por cerrada antes de revisión, validación e integración.
