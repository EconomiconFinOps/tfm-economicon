Revision JUP-131

## Code Review

**Verdict: REQUEST CHANGES**  
**Confidence: MEDIUM** para el hallazgo de exposición HTTP (evidencia de configuración y documentación oficial; endpoint no ejecutado por este agente). No se han encontrado P0/P1. El único P2 se solicita conforme a `CONTRIBUTING.md#review-and-validation-flow`, punto 3, que prescribe Request changes ante un problema.

Autor: agente independiente Codex `/root/pr161_code_review`, por la excepción humana del 24/10/2026. No representa un dictamen de Lucía Mateo ni una review publicada en GitHub. Fecha de revisión: 24/10/2026, Europe/Paris. Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.

- PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/161
- Base inmutable: `ffb5d307772f697cffb8b1e73e6330250e093601`.
- Candidato inmutable: `e730dc15fb3feb45a3b346fc9e48332c4608b049`.
- Rama: `feat/JUP-131-atlas-ecs`.
- Checkout: `C:/Users/DanteInferno/Documents/Economicon/tfm-economicon-aws-cicd`.

### Summary

La integración incorpora el Atlas aditivo de 19 ejecuciones y 1688 resultados, roles de base separados y Grafana/Prometheus en una tarea privada. La revisión del SQL, bootstrap, rutas, permisos, publicación y limpieza no ha encontrado un bloqueo funcional nuevo; sí una apertura de las métricas internas de Grafana por la nueva ruta pública. Corregir esa exposición y comprobar el delta antes de dar por satisfecha esta revisión.

### Findings

| Prioridad | Hallazgo introducido | Ubicación |
| --- | --- | --- |
| P2 | Bloquear las métricas internas anónimas bajo `/grafana/` | `infra/aws-reference/monitoring.tf:34` |

#### P2 — Bloquear las métricas internas anónimas bajo `/grafana/`

La nueva regla ALB reenvía todo `/grafana/*`, incluida `/grafana/metrics` y las métricas de plugins. CloudFront también reenvía esos paths (`infra/aws-reference/edge.tf:265`). La regla anterior `deny_metrics` sólo reconoce `/metrics` y `/metrics/*` (`edge.tf:86`), por lo que no protege la nueva subruta. El entorno del contenedor establece `GF_AUTH_ANONYMOUS_ENABLED=false`, pero no desactiva ni autentica el subsistema de métricas (`monitoring.tf:63-85`); el Dockerfile tampoco añade esa configuración.

Grafana documenta que sus métricas están activadas por defecto y que requieren configurar **su propia** autenticación básica para impedir lectura anónima. La desactivación del acceso anónimo a dashboards no cambia esa configuración. Referencias oficiales consultadas el 24/10/2026: [configuración de métricas](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#metrics) y [autenticación de métricas para evitar filtración de información](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-security-hardening/#enable-auth-for-metrics).

**Impacto:** el nuevo endpoint público permite consultar telemetría interna de Grafana sin iniciar sesión, a pesar de la intención de mantener la monitorización autenticada y del bloqueo existente de `/metrics`. No se afirma acceso anónimo a los dashboards, datos Atlas o contraseñas; el alcance del hallazgo es la exposición de telemetría.

**Reproducción a ejecutar en el entorno local desechable:** arrancar la imagen fijada con el mismo `GF_SERVER_ROOT_URL` y `GF_SERVER_SERVE_FROM_SUB_PATH=true`; solicitar `GET /grafana/metrics` sin cookies ni `Authorization`. Según la configuración documentada devuelve el endpoint de métricas; la selección de rutas de CloudFront/ALB no añade autenticación. Este revisor no ejecutó la petición ni Docker, por separación expresa del trabajo de validación. Las pruebas actuales sólo exigen 401 en `/grafana/api/search`, por lo que no detectan este caso.

**Cambio solicitado:** si no se necesitan las métricas propias de Grafana, establecer `GF_METRICS_ENABLED=false`; alternativamente bloquear `/grafana/metrics` y `/grafana/metrics/*` antes de la regla de reenvío o configurar una autenticación específica mediante secretos. Añadir un control anónimo del endpoint que falle en el candidato y pase con la corrección. La monitorización prevista sólo scrapea backend y processor, por lo que desactivar las métricas propias no afecta esas series.

### Ámbito y evidencia inspeccionada

Se leyeron `AGENTS.md`, `CONTRIBUTING.md`, la excepción PR161, el índice de continuidad y el inicio pertinente de `cloud-aws.md`, el plan `docs/planning/2026-10-24-jup131-atlas-ecs.md`, la evidencia `docs/evidence/JUP-131-atlas-ecs.md` y los requisitos/tareas OpenSpec JUP-131. Se extrajo `git diff base...candidato`; se siguieron los archivos de implementación y sus consumidores, sin usar los dictámenes anteriores como aceptación.

| Área | Conclusión de esta revisión de fuentes |
| --- | --- |
| Atlas y rollback | El importador verifica SHA256 antes de abrir transacción; elimina sólo la envoltura psql y BEGIN/COMMIT y consume los resultados del cursor dentro de `engine.begin()`. El SQL bloquea ambas tablas, compara metadatos y todas las filas existentes, rechaza colisiones y sólo inserta IDs ausentes. No hay `TRUNCATE` ni invocación de modelos en el importador. |
| Datos de origen | Comparación ejecutada de cada tupla SQL contra la salida normalizada de los dos manifiestos versionados: 19 ejecuciones/1688 resultados iguales; hashes de informes y conteos del manifiesto coherentes. Los tres dashboards coinciden con la base. |
| Roles PostgreSQL | Lector separado del propietario de metadatos; rechazo de atributos elevados, membresías y propiedad del lector, revocación de DDL/TEMP, SELECT en `evaluation`. DB `grafana` independiente en la instancia vectorial existente. Esta conclusión es estática; este revisor no ejecutó SQL. |
| TLS, subruta y sesión | Metadatos y datasource configuran `verify-full` con CA regional empaquetada; CloudFront conserva la subruta y usa política sin caché; cookies seguras, registro abierto desactivado, CSRF limitado al dominio frontend. La prueba existente ejercita cookie/Origin, pero no fue repetida por este agente. |
| Red y capacidad | Tarea Fargate sin IP pública, Grafana accesible desde SG de ALB, DB/metrics con flujos explícitos y Prometheus en loopback. 3 servicios × floor(2×150%) × 0,5 + 1 tarea monitoring × 200% × 0,5 = 5,5 vCPU. No acredita cuota ni rendimiento reales. |
| Imágenes y secretos | Bases de monitorización fijadas por digest; ECR propio con tags inmutables, Grafana y Prometheus con tags distintos y referencias de despliegue por digest. Cuatro credenciales separadas, referenciadas desde ECS, generadas fuera de Terraform. |
| Publicación y retirada | Nueva fase privada `backend-monitoring` antes de activar servicios. Plan de aplicaciones permite sólo las dos direcciones nuevas específicas; limpieza ECR incluye el repositorio propio de Grafana. Recuperación huérfana comprueba cuenta/ciclo/SHA/etiquetas y reconoce únicamente `backend-monitoring`. |
| Pruebas/CI | La nueva CI añade PostgreSQL real y smoke local de Grafana sin credenciales AWS. Lectura de sus aserciones y caminos de error; no se infiere éxito propio a partir del estado remoto informado por el coordinador. |

### Comprobaciones realmente ejecutadas

Todas las ejecuciones fueron locales y pequeñas, con Python 3.14 y biblioteca estándar; no iniciaron servicios ni construyeron clientes cloud reales.

1. `git rev-parse HEAD`, estado y diff `ffb5d307772f697cffb8b1e73e6330250e093601...e730dc15fb3feb45a3b346fc9e48332c4608b049`; HEAD coincide. `git diff --check` de ese rango: PASS, sin salida.
2. `python -B -m unittest tools.aws_demo.test_atlas_postgresql.AtlasArtifactTests tools.aws_demo.test_runner.RunnerTests.test_orphan_bootstrap_definitions_are_scoped_before_retirement -v`: **2 PASS**, 0 omitidas. El segundo usa dobles SDK.
3. `python -B -m unittest tools.aws_demo.test_monitoring.MonitoringControlTests.test_acceptance_rejects_open_access_broken_sources_and_changed_history tools.aws_demo.test_monitoring.MonitoringControlTests.test_monitoring_release_and_cleanup_are_explicitly_allowed -v`: **2 PASS**, 0 omitidas; respuestas HTTP y planes sintéticos, no HTTP real.
4. `python -B .work/pr161-code-review/static_audit.py`: **PASS**. Huella SQL `b61d9ffcc04e02d8a3df9847a7b4ffe21397d44afc5dd1d7384b7c30981a6f09`; todas las filas coinciden con fuentes canónicas, manifiesto coherente y tres dashboards sin cambios. El helper quedó en esta carpeta. Sus dos primeros intentos corrigieron una ruta del manifiesto del propio helper y su lectura de bloques INSERT (500 frente a 1688); no fueron fallos del producto.

### No realizado y límites

- No Docker, PostgreSQL real, Terraform ejecutado, build ni suites extensas; corresponden al agente de validación.
- No solicitudes a los endpoints públicos del proyecto ni reproducción HTTP del P2. La referencia web usada es documentación oficial de Grafana; no se consultó GitHub remoto ni se publicó nada.
- No AWS, credenciales, secretos, `.aws`, directorios privados, despliegue, inferencias, commits ni push. Los únicos archivos creados pertenecen a `.work/pr161-code-review/`.
- No se consumió el informe del agente de validación. La aceptación funcional del candidato completo, CloudFront/Cloud Map/RDS en AWS y la carga real siguen pendientes; los resultados históricos documentados se conservaron como históricos.
- No se reauditaron precios de AWS ni la asignación de Pontia. Los datos de coste añadidos se leyeron como estimaciones documentadas, no como límites o saldos comprobados.

### Bloqueos operativos conocidos, separados de bugs nuevos

- El usuario retiró el 24/10/2026 el techo operativo de 30 EUR de la cuenta del máster. El candidato conserva `budget_eur <= 30` en `tools/aws_demo/control.py:48`, el test y la especificación anteriores. Adaptarlo es un delta posterior pendiente; no se presenta como fallo recién descubierto de la implementación original ni habilita eliminar controles de saldo, caducidad, cuota, aceptación o autorización. No se asume límite alguno de Pontia.
- La receta mantiene deliberadamente un digest histórico de aplicación. Añadir evidencia de monitorización no acepta la aplicación completa ni habilita el despliegue.
- Según el coordinador (corte 23:07 del 24/10), las reviews, comentarios e hilos GitHub fueron leídos y estaban vacíos; CI técnica e730: 22 SUCCESS/1 SKIPPED, `JUP reviews` FAILURE por dictámenes ausentes. No se reconsultó ni reinterpretó ese estado como aprobación.
- La excepción de agentes no autoriza despliegue ni merge. Este informe no altera checks ni sustituye al segundo dictamen.

### Recommendation

Cerrar el P2 con un control explícito de las métricas de Grafana y verificar sólo el delta afectado. Conservar los gates operativos restantes y reconciliar por separado el cambio autorizado de presupuesto. Este informe se entrega al coordinador sin editar documentación compartida; la continuidad de proyecto se actualizará desde allí.
