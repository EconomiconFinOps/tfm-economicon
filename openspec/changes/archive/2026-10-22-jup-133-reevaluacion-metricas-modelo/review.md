# Revisión de JUP-133

## Verificación

- Pruebas de evaluación: los ficheros afectados por el crecimiento del conjunto versionado (SQL, filas, manifiesto, carga, atomicidad, vistas, conciliación, consultas de paneles, anotaciones, permisos y permisos con opciones de concesión) y los nuevos (inventario, identidad, documentación, actualización de una base existente y huella del gateway) pasan. No se repitió la batería completa de `evaluation-dashboard:test` en local; la ejecuta el CI del PR.
- `corepack pnpm openspec:validate` (88 de 88), `jup:check` del change, `jup:cleanup:check`, `gateway-config-hash:test` (10 de 10) y `lint` en verde.
- Grafana real: las 18 consultas SQL de los paneles responden sin error con 12 ejecuciones y 647 resultados; ver [la evidencia](../../../../docs/evidence/JUP-133-validation.md).

## Adversarial Review

Pasada 1 (ligera). Se hizo una pasada ligera, por decisión de Lucia, sobre el código de producto (huella del gateway, identidad del modelo, vistas de cambio y comparabilidad), sin el JSON de Grafana ni los documentos. Verdict: accept. Sin hallazgos bloqueantes ni altos.

| Id | Severidad | Resolución |
| --- | --- | --- |
| ADV-1 | Media | Corregido: `provider.only` con trozos de más o vacíos se rechaza en vez de descartarlos; prueba añadida. |
| ADV-2 | Baja | Aceptado: la huella incluye todo `litellm_params` salvo `api_key`, así que rotar un secreto puesto en `extra_headers` cambia la huella. La spec solo exige excluir `api_key`; ningún secreto entra en claro. |
| ADV-3 | Baja | Aceptado: una anotación `null` sobre un campo que ya trae el informe da conflicto; es coherente con «el informe manda». |

## ADR

No hace falta ADR nuevo (ADR not applicable): la identidad del modelo es una consecuencia de ADR-0022; se añadió una nota de enmienda a ese ADR que enlaza el change.

## Hallazgos del arnés

- `pnpm hu:check:pre-code` no existe en este repositorio; la puerta que pide el flujo de apply no pudo ejecutarse.
- La carga del dashboard fallaba sobre una base existente (`column generation_model_id does not exist`) porque el esquema usa `CREATE TABLE IF NOT EXISTS`. Corregido con `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` y una prueba contra PostgreSQL real.
- Muchas pruebas fijaban el número exacto de ejecuciones y filas del conjunto versionado; cada ejecución nueva obliga a editarlas a mano.

## Límites

Las cifras de la reevaluación son provisionales (una repetición, una revisora) y no permiten afirmar mejora ni empeoramiento; ver el [informe](../../../../docs/validation/model-reevaluation-report.md). Las capturas de pantalla de Grafana están pendientes.

## Human Approval

Approval type: post-review
Decision: approved
Archive decision: archive
Approved by: Lucia, 22/10/2026, después de la revisión adversarial y de las pruebas anteriores, con las cifras provisionales y los límites descritos arriba.
