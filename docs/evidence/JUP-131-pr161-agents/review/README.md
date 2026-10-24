# Revision JUP-131 — evidencia del revisor independiente

Autor: agente Codex `/root/pr161_code_review`, bajo la excepción autorizada el 24/10/2026. Estos documentos no son dictámenes humanos ni reviews publicadas en GitHub.

Orden de lectura:

1. [Revisión original](review.md), [JSON](review.json): REQUEST CHANGES sobre el candidato inmutable `e730dc15fb3feb45a3b346fc9e48332c4608b049`; un P2 sobre métricas públicas de Grafana. Se conserva intacta.
2. [Revalidación ALB](revalidation.md), [JSON](revalidation.json): APPROVE para el delta exacto de `edge.tf` y su test; cierra aquel P2.
3. [Addendum Azure](azure-review.md), [JSON](azure-review.json): APPROVE para el delta exacto de `ApiError` y su test. Explica la compatibilidad del traceback y el cambio de hash sin consumidores dependientes identificados.

La base de la revisión original es `ffb5d307772f697cffb8b1e73e6330250e093601`. Cada addendum identifica los SHA256 de sus dos archivos técnicos. Los addenda corresponden a deltas locales sobre e730, sin afirmar que constituyan un commit nuevo. Los gates de aceptación operativa siguen separados.

Comprobaciones propias incluidas:

- [static_audit.py](static_audit.py): comparación Atlas y dashboards descrita en la revisión original.
- [metrics_revalidation.py](metrics_revalidation.py) y [resultado](metrics-revalidation-check.json): evaluación local de las rutas del delta ALB.
- [azure_error_check.py](azure_error_check.py) y [resultado](azure-error-check.json): reproducción aislada del traceback y comprobaciones de compatibilidad.

Los helpers se incluyen **sin modificarlos retrospectivamente**. Presuponen su ubicación original dentro de un checkout del repositorio. Para ejecutarlos desde este paquete publicado, copiar sus archivos a `.work/pr161-code-review/` en la raíz del checkout revisado, manteniendo los archivos técnicos con los hashes documentados. No ejecutar los helpers directamente desde `docs/evidence/` ni desde una subcarpeta `publish/`.

Desde la raíz del repositorio, los comandos originales son:

```text
python -B .work/pr161-code-review/static_audit.py
python -B .work/pr161-code-review/metrics_revalidation.py
python -B .work/pr161-code-review/azure_error_check.py
```

Los dos últimos requieren que HEAD siga siendo e730 y comparan la fuente original con el delta local. Tras un commit posterior, usar un checkout desechable en ese SHA con los deltas exactos para reproducirlos; sus resultados históricos no deben alterarse para que parezcan ejecutados sobre otro commit.

Todos los enlaces relativos entre informes y evidencias propias están incluidos. Los logs del coordinador citados mediante rutas `.work/pr161-metrics-fix/` y `.work/pr161-azure-fix/` permanecen como referencias a evidencia ajena, expresamente atribuida; no se duplican sus logs o entornos aquí. No se ha leído ni incluido el informe del agente validador. `manifest.json` registra las huellas de las copias y de los cuatro archivos técnicos revisados.
