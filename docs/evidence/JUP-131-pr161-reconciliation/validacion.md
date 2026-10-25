Validacion JUP-131

Autor: agente independiente `/root/pr161_validation`, 25/10/2026. Autorización humana específica para PR161; no se atribuye este dictamen a Paris Arcos Martin ni a otro integrante humano. No se leyó el informe del otro agente.

**Veredicto: PASS para la preparación offline del candidato `812697387918c25e905a240fa35573091d9fdc16`.** Incluye la reconciliación con la aplicación aprobada, la política exclusiva de la cuenta del máster, la excepción de agentes y la renovación documentada de aceptación offline. No autoriza merge, despliegue ni ejecución de modelos. La preparación permanece bloqueada por CI de `develop` y ventana UTC.

Se leyeron AGENTS, CONTRIBUTING, la excepción PR161, el plan `docs/planning/2026-10-25-jup131-reconcile-master.md`, el índice y los apartados pertinentes de continuidad, la receta y sus evidencias. Se usó `verification-before-completion`: los resultados siguientes provienen de comandos completos y salidas comprobadas.

**Identidad del candidato y alcance incremental**

El merge-base del candidato final con `0edd11eff3458683553bd4c36f3011b77c1d3de4` es exactamente ese SHA aprobado. La reconciliación también conserva como ancestro `30d4370aca3903cf764111e451153ae2ed83510c`. Las ejecuciones iniciales de esta validación se hicieron sobre una extracción exacta de `da13f069c0f92258bb2856ff33b204cc3b176e89`; los cambios posteriores se probaron por separado.

El árbol Git `apps/` es `1c28089f0ddca7ba5de0ae08676da1ed353b450c` tanto en da13 como en bfffb88b, 964c9f55 y el candidato final. Los deltas bff/964 sólo cambian la excepción PR161 y su test; los deltas 3062/812 sólo cambian `release.json` y el recibo de aceptación. Controlador, aplicaciones y workflows permanecen idénticos a los bytes probados en da13. No se presenta una ejecución anterior como una repetición sobre otro SHA.

Toda `apps/azure-cost-api/` coincide con 0edd11ef. `ApiError` conserva `@dataclass(frozen=True)` y su blob `a5ff184e4729d2248a3ff12c3001f3076f2ccdff`; la regresión añadida para la solución mutable del 24/10 se retiró. Los SHA256 de contenido Git son:

| Archivo | SHA256, idéntico al aprobado |
| --- | --- |
| `apps/azure-cost-api/app/errors.py` | `2f6612520f6001475ce63e49819c8492e61afd05beb67c9f905d438e0c6ba1a5` |
| `apps/azure-cost-api/requirements.txt` | `248b7d6f6140e3be28eeea0fa5ce4afa583e540f0f070c8bdadadef04c76c23b` |
| `apps/azure-cost-api/requirements-dev.txt` | `be50d4dbd8354c7c1969344c05a03aff47a0a5eba1e3adcb7e16df1f1d9288e4` |

**Comprobaciones propias del 25/10**

| Criterio | Prueba efectiva y resultado |
| --- | --- |
| Azure aprobado y pin vigente | Suite completa: **81 PASS**, exit 0. Runtime comprobado: Python 3.14.4, FastAPI 0.162.0, Starlette **1.9.0**, pytest 9.1.1 y httpx 0.28.1. Un aviso de deprecación de TestClient. |
| Presupuesto exclusivo del máster | `validate_config` acepta la política `master-account-authorized-2026-10-24` sólo en `323188184300`, sin `budget_eur` ni `available_credit_eur`. Rechaza otra cuenta/política y la introducción de presupuesto o saldo inventados. La cuenta ordinaria mantiene el techo anterior. |
| Guardas conservadas | **48 PASS**, exit 0, en control, runner y regresiones: SHA, región, configuración, cuotas 6/1 simuladas, expiración, plan y fases, recursos ajenos, privacidad del entorno y aceptación. Aprobación manual presente en Terraform; no se ejecutó el pipeline. |
| Revisión ordinaria y excepción PR161 | **111 PASS**, exit 0, sobre da13: política general/PR135 y siete grupos PR161. Comprueban identidad/rama/base/roles, declaración visible, informes íntegros e independientes, candidato/HEAD, rechazo de código posterior, informe faltante, autor de agente reutilizado, dictamen negativo y requests for changes pendientes. |
| Primer identificador JUP | RED propio contra da13: el caso `JUP-140: references JUP-131` obtiene indebidamente aceptación; **1 FAIL esperado**, exit 1. Con bff: **7 PASS**. El candidato final conserva la corrección. |
| ID y cuatro roles duplicados | Cinco casos propios separados contra bff reproducen el bypass de ID con espacios y etiquetas de roles con distinta capitalización: **5 FAIL esperados**, exit 1. En 964: **12 PASS**, exit 0, sumando los cinco casos propios y los siete oficiales. Los archivos de política son idénticos en el candidato final. |
| Preparación y restantes bloqueos | Probe propio: **19 rechazos esperados**, incluidos SHA/CI erróneos, CI de PR o rama, CI fallida, falta de ascendencia, caducidad vencida o superior a ocho horas, región y estimación inválidas. Entradas sintéticas explícitas, sin consultar saldo ni AWS. |
| Receta final y aceptación | Sobre archivo exacto de 812: **5 PASS**, exit 0, en `test_release_readiness`; `validate_recipe` y `validate_recipe_files` conformes. Evidencia alterada/ausente/fuera del árbol, scripts inválidos y deriva de aplicación siguen bloqueados. |
| Preparación final del máster | Se generan ficheros locales con la política del máster y SHA 812, bloqueando llamadas a procesos/red dentro de `prepare`. `aws_deployable=false`, `aws_preflight_executed=false`, `aws_resources_created=false`. Sólo quedan `ci_run_id` y `expires_at` pendientes; desaparece el bloqueo por digest histórico. |

La preparación final se probó con un fixture propio, no con la configuración real administrada por el coordinador. No se afirma que la estimación sintética ni ningún saldo estén verificados. El validador de configuración comprueba la forma de la ventana; el runner exige además que venza dentro de las ocho horas siguientes y vuelve a comprobarla antes de aplicar.

Comandos ejecutados en copias propias bajo `.work/pr161-reconciliation-validation/`, nunca desde `docs/evidence`:

```text
python -m pytest tests -q -p no:cacheprovider --basetemp=<temporal propio>
# cwd source/apps/azure-cost-api: 81 PASS.
python -m unittest tools.aws_demo.test_control tools.aws_demo.test_runner tools.aws_demo.test_review_fixes -v
# cwd source: 48 PASS.
node --test tools/pr-policy.test.mjs tools/pr161-agent-evidence.test.mjs
# cwd source: 111 PASS.
node --test --test-name-pattern="exception fails closed" tools/pr161-agent-evidence.test.mjs
# cwd primary-jup-red: RED esperado; luego siete casos oficiales GREEN en source-bff.
node --test tools/independent-role-edges.test.mjs
# cwd duplicate-roles-red: cinco RED esperados.
node --test tools/pr161-agent-evidence.test.mjs tools/independent-role-edges.test.mjs
# cwd source-964: 12 PASS.
python -m unittest tools.aws_demo.test_release_readiness -v
# cwd source-final: 5 PASS.
python .work/pr161-reconciliation-validation/revalidate_release.py
# snapshot Git 812, integridad de receta/evidencias y prepare bloqueado conformes.
```

Node 24.14.1. Las suites se ejecutaron fuera del sandbox de Windows, que anteriormente bloqueó temporales, con entorno mínimo, temporales propios, caché pytest desactivada y sin credenciales. Los repositorios Git de los tests de política son fixtures temporales propios; no se modificaron archivos versionados ni commits de la rama.

**CI consultada directamente y aceptación offline**

Consulta propia a GitHub el 25/10 a las 11:13:50 UTC: [CI de PR 40187165537](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40187165537), [CI push 40187163124](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40187163124) y [SQL 40187165282](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40187165282) están SUCCESS sobre **da13**. Se comprobaron los once jobs de la CI principal y se leyeron directamente ocho logs, no sólo la comunicación del coordinador.

| Evidencia remota leída | Resultado |
| --- | --- |
| Backend / processor | 2732 PASS, 369 SKIP, 19571 avisos / 2674 PASS, 150 SKIP, 2388 avisos |
| Frontend / Azure | 1427 PASS en 96 archivos / 81 PASS y un aviso |
| PostgreSQL real | 45 PASS pgvector y un aviso; 8 pruebas operacionales/Atlas conformes |
| Grafana real aislado | Tres dashboards, 19/1688, datasource saludable, acceso anónimo denegado, sesión permitida, origen ajeno denegado y preferencias conservadas tras reinicio |
| Control / Terraform | 90 casos: 83 PASS y 7 SKIP; 14 mocks de referencia y 1 de bootstrap PASS |
| SQL nativo adicional | Backend 54 PASS y 88 avisos; processor 8 PASS |

Estas ejecuciones son de GitHub Actions; no son pruebas locales de este agente ni ejecución AWS. Los skips se conservan como omisiones. El job SQL opt-in separado y el smoke real aportan la evidencia actual de PostgreSQL/Grafana; no se reutilizan los resultados del 24/10 como pruebas frescas. El check separado `JUP reviews` de da13 figuraba FAILURE al consultar sus runs; los informes y el manifiesto de esta entrega todavía debían publicarse. No se declara verde la política de un head posterior por esos runs.

La CI completa del árbol de aplicación, las pruebas propias del delta y la identidad de sus archivos **son suficientes para renovar la aceptación offline del código**; no falta otra suite local para ese alcance. El recibo nuevo registra exactamente ese límite. Se verificó que las cinco evidencias históricas y sus hashes permanecen iguales; se añadió el recibo de reconciliación sin cambiar bootstrap, checks, modelos o entorno de aplicación.

- `application_sha256`: `5e19f3f4ff0db6039ebc42b2733d9dd4266e94b55c6fc8fac741c21876461e70`.
- SHA256 de `infra/aws-cicd/release.json`: `0485223b5f9cfb94f27abf745d11929c010a65d9880b297917231aa9318b1206`.
- SHA256 de `application-acceptance.md`: `5eb418403fcf3dcc0dbccde23c7423e38f138da2cb2b206eee400f4afa87a3f0`.

El digest de aplicación cubre `apps/`; ECS/control quedan ligados por el SHA del candidato y sus pruebas. La CI de da13 se transfiere por identidad de esos bytes, con revalidación explícita de los archivos posteriores. No se afirma que ya exista CI remota de 812. Tampoco la CI push de una rama sustituye la CI push del SHA exacto de `develop` que exige el runner.

**Límites y entrega**

Sin AWS, lectura de secretos, inferencias, Docker adicional, builds/pipelines AWS, despliegue o merge. No se construyeron aquí las imágenes finales de release. Cognito/Bedrock están cubiertos offline por mocks; sus permisos, login y respuestas reales, RDS/CloudFront/ECS, DNS, cuota efectiva y el checker funcional permanecen para sus fases autorizadas. La aceptación offline no marca `application_ready` ni autoriza el ensayo.

No quedan defectos reproducidos abiertos en el alcance validado. Los dos bypasses de política anteriores conservan su RED y corrección; los dictámenes y resultados del 24/10 siguen siendo históricos de sus candidatos.

Publicables: este `validacion.md` y `validacion.json` íntegros, con hash normalizado LF. Logs, scripts, extractos de CI y pruebas de identidad permanecen en `.work/pr161-reconciliation-validation/`; el JSON incluye comandos, resultados y huellas. No publicar archives, copias de fuente, entornos ni configuraciones sintéticas de arranque. La continuidad y la publicación de la evidencia corresponden al coordinador.
