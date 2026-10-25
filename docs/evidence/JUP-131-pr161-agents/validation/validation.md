Validacion JUP-131

Autoría: agente independiente `/root/pr161_validation`, 24/10/2026, por la excepción humana documentada en `docs/evidence/JUP-131-pr161-agent-exception.md`. Este informe no se atribuye a Paris Arcos Martin ni acredita participación humana en las pruebas.

Candidato exacto: `e730dc15fb3feb45a3b346fc9e48332c4608b049`, PR161; base `ffb5d307772f697cffb8b1e73e6330250e093601`. Alcance: **PREPARACIÓN** de la carga aditiva Atlas y monitorización ECS. No incluye aceptación completa de la aplicación, despliegue, merge ni aprobación de plataforma.

**Veredicto del candidato e730: REQUEST CHANGES.** Las pruebas originales de SQL, Grafana, controlador y Terraform pasan. En una comprobación posterior solicitada por el coordinador, el nuevo escenario de privacidad de rutas falla con `edge.tf` original: la regla que responde 404 sólo contiene `/metrics` y `/metrics/*`, y deja fuera `/grafana/metrics` y sus subrutas. Evidencia propia: [RED del contrato ALB](delta-red-monitoring-original-edge.log), 1 PASS / 1 FAIL. Esto reproduce la carencia de la regla Terraform; no es una prueba HTTP de `/grafana/metrics` sobre un ALB real. La comprobación posterior del delta de dos archivos se registra separadamente en [delta-validation.md](delta-validation.md).

Se leyeron AGENTS, CONTRIBUTING, la excepción, el índice y comienzo pertinente de continuidad, `docs/planning/2026-10-24-jup131-atlas-ecs.md`, `docs/evidence/JUP-131-atlas-ecs.md` y los requisitos de `openspec/changes/jup-131-aws-cicd-defensa/specs/aws-defense-lifecycle/spec.md`. No se leyó el informe del otro agente. La ampliación de rutas fue solicitada por el coordinador y no se presenta como un descubrimiento independiente original.

**Criterios y evidencia nueva**

| Criterio | Resultado observado | Evidencia |
| --- | --- | --- |
| Artefacto exacto y 19 informes canónicos | PASS. SQL SHA256 `b61d9ffcc04e02d8a3df9847a7b4ffe21397d44afc5dd1d7384b7c30981a6f09`; manifiesto y hashes canónicos comprobados. | [suite Atlas real](remote/atlas-postgresql-real.log) |
| Primera carga 19 runs / 1688 resultados | PASS en PostgreSQL 16.15 real. | misma suite, `test_additive_idempotent_and_preserves_unrelated_history` |
| Repetición y preservación de datos adicionales | PASS. Tras insertar un run y resultado propios: 20/1689, conservados en dos importaciones posteriores. | misma suite |
| Conflicto de identidad sin importación parcial | PASS. Huella de identidad cambiada y otro run retirado: la importación falla y mantiene el estado previo. | misma suite, `test_conflicting_identity_aborts_without_partial_import` |
| Conflicto de resultado sin sobrescritura | PASS adicional. Se alteró un resultado y retiró un run: error PostgreSQL `P0001`; snapshot de todas las filas idéntico antes/después (`7dc753c2e9ed51905c5a6e911fa580ebca1a52345622a834e96ffe7b6f5b8e89`). | [casos SQL adicionales](remote/atlas-extra-real-rerun.log) |
| Artefacto inválido rechazado antes de cambios DB | PASS. SQL alterado no crea ni el esquema `evaluation`. | suite Atlas real |
| Lector SELECT sin DML/DDL/TEMP | PASS. SELECT funciona; INSERT, UPDATE, DELETE, TRUNCATE, CREATE en evaluation/public, TEMP y CREATE SCHEMA se rechazan con SQLSTATE `42501`. | suite Atlas y casos adicionales |
| No adoptar lector privilegiado o propietario | PASS. Rol CREATEDB y rol propietario de otro esquema rechazados. | suite Atlas y casos adicionales |
| Metadatos separados y persistentes | PASS. DB `grafana` con propietario distinto; tabla conservada tras repetir configuración, ausente en DB de evaluación. Lector sin CONNECT a grafana y propietario de metadatos sin SELECT de evaluación. | suite Atlas y casos adicionales |
| Tres dashboards, incluido narrativo con cinco secciones | PASS. Los tres JSON son idénticos byte a byte a la base; UIDs y cinco filas narrativas comprobados. Grafana devuelve los tres dashboards con paneles. | [artefactos](artifact-release-checks.json), [smoke](remote-monitoring-console.log) |
| Imágenes Grafana 11.3.0 / Prometheus 2.55.1 fijadas | PASS. Construcción real desde los Dockerfiles del candidato y bases por digest. Grafana de prueba añade sólo CA sintética para PostgreSQL aislado. | smoke y [recursos](remote/resources.jsonl) |
| TLS de ambos accesos PostgreSQL y salud de datasources | PASS en el smoke con CA sintética, `verify-full`, metadata y datasource PostgreSQL funcionales; Prometheus healthy. No es TLS contra RDS AWS. | smoke |
| Autenticación, cookie y CSRF | PASS en rutas ejercitadas: `/grafana/api/search` anónimo responde 401; login genera cookie Secure; consulta POST con cookie funciona con Host/Origin distintos; Origin ajeno devuelve 403 sin cambiar preferencias. No extrapolar este 401 a todos los endpoints. | smoke |
| Reinicio y persistencia de preferencias | PASS. Tras reiniciar Grafana, segunda prueba devuelve `preferences_retained=true`, conserva homeDashboardUID, fuentes y datos. | smoke |
| Privacidad completa de rutas de métricas | **REQUEST CHANGES en e730**. El escenario adicional no encuentra denegación de `/grafana/metrics` y `/grafana/metrics/internal`. Login/health/API se conservan en la comprobación. | RED del contrato ALB; delta separado |
| `/grafana` sin reescritura ni caché; rutas privadas | PASS en mocks Terraform: dos comportamientos CloudFront, sin función API; ALB→Grafana 3000, Grafana→DB 5432, scraping privado 8000/8001, sin IP pública. No se probó CloudFront/Cloud Map real. | [Terraform 13](terraform-aws-reference-test.log) |
| Dos réplicas de cada app y máximo rolling 5.5 vCPU | PASS en mocks: apps 150% = 4.5 vCPU, monitoring 200% = 1 vCPU; una tarea monitoring 0.5 vCPU / 1 GiB. No acredita cuota efectiva AWS. | Terraform 13 |
| Bootstrap privado, imágenes inmutables y cuatro secretos separados | PASS simulado: secuencia schemas→fixtures→monitoring; referencias en vez de valores; cuatro valores sintéticos distintos y conservados en reintentos; rechazo de imágenes o recursos ajenos. | [controlador 65](controller-targeted-windows-unsandboxed.log) |
| Release, expiración y retirada delimitada | PASS simulado: rechazo de fuente/plan/cuenta/fase ajenas, fuente sin CI develop exacta, expiración, reemplazos de datos y definición huérfana fuera de alcance; limpieza parcial no crea recursos. | controlador 65; [bootstrap Terraform](terraform-aws-bootstrap-test.log) |
| Evidencia histórica no habilita la app actual | PASS como rechazo esperado: integridad documental válida, pero `validate_recipe_files` falla por digest de aplicación distinto. | artefactos/release |
| Guarda histórica 30 EUR y saldo conocido | Comportamiento técnico confirmado: 30.01 / 60 EUR, saldo None / 0 / NaN, estimación infinita o superior al saldo rechazados. **Regla operativa retirada por el usuario el 24/10**; adaptación pendiente separada, sin inventar límite Pontia. | artefactos/release y controlador 65 |

**Ejecuciones reproducibles**

Los logs completos, metadatos de ejecución y scripts del agente se conservaron en `.work/pr161-validation/`. Este paquete publicado contiene informes y salidas finales; no implica ejecución desde docs/evidence. No se modificaron fuentes/tests versionados.

Salidas adicionales: [backend 22](backend-bootstrap-targeted-windows-unsandboxed.log), [processor 4](remote/processor-bootstrap-linux.log) y [routing 8](edge-functions.log).

```text
python -m unittest tools.aws_demo.test_atlas_postgresql -v
# DockerServer, PostgreSQL 16.15 / Python 3.12.13: 7 PASS, 0 skips.
# 6 escenarios PostgreSQL reales + comprobación de artefacto.

python .work/pr161-validation/sql_extra.py
# DockerServer, mismas dependencias: cinco grupos adicionales PASS.

python -m unittest tools.aws_demo.test_monitoring tools.aws_demo.test_control tools.aws_demo.test_bootstrap tools.aws_demo.test_private_tasks tools.aws_demo.test_runner tools.aws_demo.test_review_fixes -v
# Windows / Python 3.14.4 sobre extracción exacta e730: 65 PASS.

python -m pytest tests/test_aws_bootstrap_jup131.py tests/test_bootstrap_contract_jup131.py tests/test_bootstrap_identity_jup131.py -q -p no:cacheprovider
# cwd apps/backend: 22 PASS, 12 advertencias datetime/sqlite.

python -m pytest tests/test_aws_bootstrap_jup131.py -q -p no:cacheprovider
# cwd apps/processor, imagen de tests Python 3.12 en DockerServer: 4 PASS.

python tools/aws_demo/monitoring_smoke.py
# Código de e730, instrumentado sólo en namespace/labels/auditoría y build --network none:
# primer arranque y reinicio PASS; tres UIDs, 19 identidades/hashes y 1688 resultados.

terraform fmt -check -recursive <copias propias de ambos roots>
terraform -chdir=<copia propia> init -backend=false -input=false -lockfile=readonly
terraform -chdir=<copia propia> validate
terraform -chdir=<copia propia> test
# Terraform 1.13.3, proveedor AWS 6.13.0 cacheado, sólo mocks:
# aws-reference 13 PASS y aws-bootstrap 1 PASS; fmt/validate exit 0.

node infra/aws-reference/tests/edge-functions.test.cjs
# 8 escenarios de routing PASS.
```

El smoke real fue invocado por `remote_validation.py monitoring`; la fuente original del smoke tiene SHA256 `b38eb3040a17eacce49e843cf6045303be3fefee8278bd55d802a6dac41feb3d`. La instrumentación sustituye únicamente el prefijo literal por `pr161-validation-mon-`, añade etiquetas de propiedad, desactiva red del build y registra recursos. No se cambió la lógica de login, consultas, hashes, CSRF ni reinicio. La comprobación de datasource SQL compara cada uno de los 19 identificadores, hashes y conteos; no ejecuta todas las consultas de todos los paneles.

**Identidad, aislamiento y limpieza**

El archivo local `source-e730.tar` se obtuvo con `git archive` del SHA exacto: 56.678.400 bytes, SHA256 `be92192370bd546b0829e549bb2c61b0729a484169ddab8cf5038eaf69784db2`; `git get-tar-commit-id` confirma e730. Se extrajo a `candidate-source/` antes de los cambios posteriores del coordinador.

No había daemon Docker local: contexto por defecto remoto TCP 2375 y contexto desktop-linux sin tubería; no se utilizó ese endpoint TCP. La revisión automática rechazó exportar el checkout a DockerServer. Tras acreditar que el repositorio es público y el servidor es el destino documentado del proyecto, aprobó la alternativa: el propio DockerServer descargó SIN autenticación el tarball público e730 y verificó sus 2603 blobs contra el árbol `d9c99623ce05f541239c206a6c489ca991541a9b`. No se exportó el checkout privado. Recibo: [public-source-proof.json](remote/public-source-proof.json); archivo GitHub SHA256 `26bb21419d35b0e7a5f81c94dd4e69b31347391cdcb8c2e8b8b48d4b1ae51ea4`.

Ubicación de ejecución Docker: **DockerServer/dockerserver**, Docker 29.6.2, vía SSH BatchMode y socket Unix del host. Fuente propia: `/tmp/pr161-validation-e730-20261024-2125/source`. Las pruebas no se ejecutaron en Docker de este PC ni en AWS.

PostgreSQL arrancó con `--network none`; los helpers y Grafana/Prometheus compartieron exclusivamente ese namespace; processor usó red `none`. Cero puertos publicados. Sólo se montó la extracción propia como sólo lectura; no hubo volúmenes de datos existentes. Contenedores limitados a 1 CPU / 768 MiB o 1.5 GiB; probe 0.5 CPU / 128 MiB. Los IDs de imágenes de tests reutilizadas y todas las instancias están en `remote/resources.jsonl`; se conservaron las imágenes preexistentes.

[Limpieza verificada](cleanup-summary.json): 10 contenedores propios ausentes por ID, 3 tags de imágenes de prueba ausentes y 3 volúmenes anónimos propios ausentes. No se ejecutó ninguna limpieza global ni comandos mutadores dirigidos a servicios ajenos. El directorio temporal de fuentes/evidencia no es un servicio en ejecución.

**Incidencias del entorno y del harness, resueltas o delimitadas**

- Primera ejecución Windows: 14 errores de controlador y errores de setup pytest por `WinError 5` sobre temporales del sandbox. Los logs iniciales se conservan. La repetición autorizada fuera del sandbox sobre el archive e730 dio 65/65 y 22/22. No se cambiaron tests de producto.
- Processor Windows dio 3 PASS / 1 error por `tiktoken` ausente. En la imagen de tests ya disponible y sin red dio 4/4 PASS.
- El primer harness SQL adicional esperaba que libpq expusiera SQLSTATE 42501 al denegar CONNECT. La conexión fue denegada correctamente, pero el código fue None. Se corrigió únicamente el harness para exigir ese error específico y comprobar además `has_database_privilege(...,'CONNECT')=false`; repetición focal PASS. Logs inicial y repetición conservados.
- Un intento del filtro Terraform con separadores `/` en Windows ejecutó 0 pruebas: se descartó. Con separador nativo ejecutó los dos escenarios y produjo el RED real. Un problema de codificación de stdout del harness se corrigió; los logs completos ya estaban guardados. No se contó un exit 0 sin pruebas como aprobación.

**Lo no validado y límites del dictamen**

No se ejecutaron AWS, despliegues, builds/pipelines cloud, modelos, Cognito real, Bedrock real, RDS real, publicación ECR, cuotas, saldo de cuenta ni retirada AWS. No se accedió a `.aws`, credenciales ni private-evaluator. No se modificaron GitHub/Trello/Discord, no hubo commits/push ni subagentes.

El smoke usa PostgreSQL 16.15 con CA sintética; la suite SQL aislada usa loopback sin TLS y un administrador PostgreSQL de prueba. No acredita permisos del administrador RDS ni la CA/región real. Las rutas CloudFront/ALB y Cloud Map se comprueban con configuración/mock, no atravesando AWS. No se prueban visualmente los dashboards, todas sus consultas de panel ni el scraping de las apps reales. Tampoco se ejecuta el programa completo de pruebas de aplicación o aceptación de modelos.

El digest aceptado en la receta sigue siendo `8a47bf3d8f88fbc45652bdcbe5ecb7f71c036c3e9d3bfc0b51bb556d36cd633d`; el digest calculado del candidato es `4855445e350f6d2e301ca4cd8ec3771616b8c8e25921e304e6ab33246d4338fd`. La aceptación parcial de Atlas no renueva la aplicación completa. La guarda 30 EUR sigue siendo un comportamiento histórico pendiente de adaptación a la instrucción actual del usuario.

CI e730 comunicada por el coordinador: 22 SUCCESS / 1 SKIPPED y `JUP reviews` FAILURE, sin reviews publicadas. Es evidencia ajena anterior; este agente no la volvió a consultar ni la presenta como CI completamente verde. El dictamen anterior asistido y la evidencia histórica de la documentación tampoco se cuentan como ejecuciones de este agente.

Ampliación posterior: el coordinador comunicó fallos Azure en el run `40133534310` del mismo e730. Se reprodujo el fallo en una copia propia y se validó el delta Azure por separado en [azure-delta-validation.md](azure-delta-validation.md). No se repitieron SQL/Grafana ni se alteraron el alcance o dictamen inicial de este informe.
