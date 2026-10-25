Revision JUP-131

**Veredicto actualizado: APPROVE**, para el candidato `e730dc15fb3feb45a3b346fc9e48332c4608b049` más el delta de dos archivos identificado abajo. El único P2 queda cerrado en la revisión de fuentes. No se encuentran nuevos P0/P1/P2 en el delta. Este dictamen no atribuye un commit nuevo ni acredita despliegue o aceptación operativa.

Autor: agente independiente Codex `/root/pr161_code_review`, bajo la excepción autorizada el 24/10/2026. No es un dictamen de Lucía Mateo ni una review publicada en GitHub. Revalidación: 24/10/2026, 23:28 Europe/Paris. PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/161.

La revisión original [review.md](review.md) y su [JSON](review.json) se conservan sin modificaciones, con REQUEST CHANGES sobre el candidato original. Base de esa revisión: `ffb5d307772f697cffb8b1e73e6330250e093601`. HEAD comprobado durante esta revalidación: `e730dc15fb3feb45a3b346fc9e48332c4608b049`; rama `feat/JUP-131-atlas-ecs`.

| Archivo del delta local | SHA256 de los bytes revisados |
| --- | --- |
| `infra/aws-reference/edge.tf` | `e78050dcc2d0b4f4ce76c1e3c9b64537c25a995e4b1537915dc3e7285726e2e7` |
| `infra/aws-reference/tests/monitoring.tftest.hcl` | `d215fb2d3ea7d759a6a2a276b60e7541d2ce77e7ef9031f75972437ce5864c9f` |

### Cierre del hallazgo y riesgos del cambio

`edge.tf:87` añade `/grafana/metrics*` a la regla existente `deny_metrics`. El asterisco cubre tanto la ruta exacta como su barra final y subrutas. La regla devuelve 404 y tiene prioridad 1 (`edge.tf:75-80`), antes del reenvío a Grafana de prioridad 10 (`monitoring.tf:28`). No restringe el método HTTP. Las rutas Grafana de CloudFront conservan el path, por lo que la denegación se aplica al tráfico reenviado por ese comportamiento.

Se contrastó la semántica con la [documentación oficial de condiciones ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-condition-types.html), consultada el 24/10/2026: `*` admite cero o más caracteres; hay un máximo de tres comparaciones por condición y cinco por regla, y hasta cinco comodines por regla. Este delta contiene tres valores y dos comodines. Las condiciones examinan el path después de normalizar la URI, sin incluir la query string.

El bloqueo por prefijo también alcanza nombres como `/grafana/metrics-prefix`. Es una ampliación deliberada del bloqueo de telemetría y no colisiona con las rutas de login, health, consultas, dashboards, estáticos o websocket revisadas. No cambia la configuración interna de Grafana ni el scraping de backend/processor, y no altera roles, TLS, SQL, capacidad o limpieza.

El nuevo run `metrics_routes_are_denied_before_grafana` (`monitoring.tftest.hcl:36-63`) comprueba métricas raíz/subrutas, rutas útiles preservadas, respuesta fija 404, precedencia y máximo de tres comparaciones. Para los literales actuales, la conversión `*` a `.*` anclada tiene la semántica requerida; los patrones no contienen otros metacaracteres regex. No se detecta una regresión introducida por el test.

### Comprobaciones y procedencia

- Ejecutado por este revisor: lectura del diff de ambos archivos, su contexto de CloudFront/ALB y el test completo; `git diff --check -- infra/aws-reference/edge.tf infra/aws-reference/tests/monitoring.tftest.hcl`: PASS.
- Ejecutado por este revisor: `python -B .work/pr161-code-review/metrics_revalidation.py`: PASS. Compara con `git show e730dc15fb3feb45a3b346fc9e48332c4608b049:infra/aws-reference/edge.tf`, confirma que las dos rutas Grafana de métricas no se bloqueaban en e730 y que el nuevo patrón bloquea ocho casos y preserva nueve. Comprueba además prioridad, 404, número de valores, comodines y hashes. Evidencia: [metrics-revalidation-check.json](metrics-revalidation-check.json); helper: [metrics_revalidation.py](metrics_revalidation.py).
- Evidencia suministrada por el coordinador y leída, **no ejecutada por este revisor**: `.work/pr161-metrics-fix/red-monitoring.log`, 1 PASS/1 FAIL. El test nuevo falla precisamente ante los dos valores antiguos, mientras la comprobación previa pasa. Es evidencia negativa útil de la regresión, no una ejecución HTTP.
- Registro GREEN suministrado por el coordinador y leído al cierre: `.work/pr161-metrics-fix/verification.json`, fechado 21:29:20 UTC. Declara `terraform fmt` y `validate` PASS y 14 tests mock PASS/0 FAIL sobre los mismos dos hashes. Se conserva la atribución al coordinador: este revisor no ejecutó Terraform ni auditó el log completo de GREEN. No se ha leído el informe del agente validador.
- Los cuatro tests pequeños y la comparación de 19 ejecuciones/1688 resultados descritos en la revisión original siguen siendo evidencia de aquella revisión; no se presentan como repetidos en este delta.

### Límites y continuidad

La comprobación propia evalúa patrones de fuentes sobre rutas normales; no reproduce la normalización URI del servicio. No se ejecutaron Terraform, Docker, AWS, HTTP, SQL ni suites extensas. El resultado GREEN procede del registro del coordinador y no se consumió el informe del agente validador. La validación de runtime y del candidato completo corresponde a su evidencia separada.

Las modificaciones documentales del coordinador no forman parte del delta técnico revalidado. Si cambia alguno de los dos hashes, este dictamen no certifica automáticamente la versión posterior. La guarda histórica de 30 EUR continúa como delta operativo pendiente ya identificado; esta revalidación no la adapta ni presupone límites de Pontia. Se mantienen los gates de aceptación, saldo, caducidad, cuota y autorización señalados en el informe original.

No hubo acceso a secretos ni credenciales, publicaciones, commits o push. Los únicos archivos escritos por este revisor están en `.work/pr161-code-review/`. El coordinador es responsable de incorporar la atribución real y estos resultados a la documentación compartida y de combinar ambos dictámenes.
