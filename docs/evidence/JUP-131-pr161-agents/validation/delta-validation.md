Validacion JUP-131

Revalidación del delta ALB por el agente `/root/pr161_validation`, 24/10/2026. Es un dictamen de agente y no se atribuye a Paris Arcos Martin. Complementa [la validación del candidato original](validation.md).

**Veredicto: PASS para el delta local de dos archivos identificado abajo.** La regresión falla contra `edge.tf` de e730 y pasa con la corrección; `fmt`, `validate` y los 14 escenarios mock del root `aws-reference` pasan. No equivale a aprobar retroactivamente e730 ni a validar un futuro commit con otros cambios.

La solicitud posterior del coordinador limitó la comprobación a la denegación ALB de las rutas de métricas, sin cambios en SQL, imágenes o aplicación. Snapshot propio: `2026-10-24T21:28:49.181977Z`, sobre base `e730dc15fb3feb45a3b346fc9e48332c4608b049`. No se heredó el dictamen del otro agente ni se leyó su informe; se ejecutaron las comprobaciones siguientes sobre una copia propia.

| Archivo del delta | SHA256 exacto de los bytes probados |
| --- | --- |
| `infra/aws-reference/edge.tf` | `e78050dcc2d0b4f4ce76c1e3c9b64537c25a995e4b1537915dc3e7285726e2e7` |
| `infra/aws-reference/tests/monitoring.tftest.hcl` | `d215fb2d3ea7d759a6a2a276b60e7541d2ce77e7ef9031f75972437ce5864c9f` |

[Manifiesto](delta-manifest.json): incluye las huellas anteriores, las del candidato original, fecha, resultados y condición de delta local todavía sin commit en el momento de la prueba.

| Comprobación fresca | Comando y resultado |
| --- | --- |
| RED: nueva regresión con reglas originales | `terraform -chdir=<copia propia> test -filter=tests\monitoring.tftest.hcl -no-color` → exit 1, 1 PASS / 1 FAIL. Falta el patrón que cubre `/grafana/metrics` y `/grafana/metrics/internal`. [Salida](delta-red-monitoring-original-edge.log). |
| Formato del root corregido | `terraform fmt -check -recursive <copia propia>` → exit 0. [Salida](delta-terraform-fmt.log). |
| Validación del root corregido | `terraform -chdir=<copia propia> validate -no-color` → exit 0. [Salida](delta-terraform-validate.log). |
| GREEN: suite mock completa del root corregido | `terraform -chdir=<copia propia> test -no-color` → exit 0, 14 PASS / 0 FAIL. [Salida](delta-green-terraform-test.log). |

La nueva regla incorpora `/grafana/metrics*`, conserva `/metrics` y `/metrics/*` y mantiene tres valores. La prueba comprueba respuesta fija 404 y prioridad anterior al forward de Grafana; las rutas `/grafana`, `/grafana/login`, `/grafana/api/health` y `/grafana/api/ds/query` no coinciden con la denegación. También pasan los escenarios existentes de rutas privadas, task shape, réplicas, rolling 5.5 vCPU, TLS/referencias de secretos y apagado por defecto.

Terraform 1.13.3 y proveedor AWS 6.13.0 cacheado; `init -backend=false`, sin configuración de credenciales y sólo mocks. El origen de ejecución es `.work/pr161-validation/terraform/infra/aws-reference`, nunca `docs/evidence`. Argumentos `-chdir` se pasaron por separado mediante subprocess. Un primer filtro con `/` en Windows ejecutó 0 pruebas y se descartó; no se contó como evidencia. El filtro nativo ejecutó y reprodujo la aserción concreta. Un error de codificación de stdout del harness se corrigió sin alterar fuentes/tests ni los logs completos ya capturados.

No se repitieron SQL/Grafana después de este éxito: el delta no modifica sus archivos y ya existe evidencia fresca del e730 en el informe base. No se construyeron nuevas imágenes ni se crearon recursos Docker en esta revalidación. La auditoría del informe base confirma retirada de 10 contenedores, 3 tags propios y 3 volúmenes anónimos por identidad en DockerServer.

**Límites:** la regla se verifica con Terraform/mock, sin ALB/CloudFront reales. No se hizo una petición HTTP a `/grafana/metrics` en AWS; el hallazgo reproducido es la falta del bloqueo en el contrato de rutas. Continúan pendientes la CI del commit que integre exactamente este delta, la aceptación completa de la aplicación y cualquier autorización de despliegue/merge. La guarda histórica 30 EUR aún debe adaptarse a la instrucción actual del usuario; este delta no la cambia ni acredita un límite Pontia.
