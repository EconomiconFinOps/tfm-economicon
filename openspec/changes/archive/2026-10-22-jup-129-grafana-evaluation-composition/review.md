# JUP-129 — cierre técnico previo al archivo

22/10/2026, proceso CONTRIBUTING 2026-10-18. Rama feat/JUP-129-grafana-evaluation-composition; HEAD 07ef55580c100885ffc8075e82fb7b2eb0011ce3 y develop c00063dbaa83a1237431edef9de6d71d1bfd1ffd integrado sin commit por PM. Los bytes del merge no se atribuyen sólo al HEAD.

## Dictámenes y alcance

Revisor R4 independiente: REVIEW_PASS, tres pruebas propias de empaquetado/topología PASS. Validador R4 distinto: VALIDATION_PASS técnico focal, comparación propia de configuración resuelta y entradas, cobertura R3/R2 ratificada por identidad. Originales completos y borradores custodiados por PM, sin reescritura. Manifiestos: Revisor 5d3bb7c81907959c7a485aa003b0c9a55678d065cd3216d809b0603c18868c46; Validador f2affe556c347f12f05036eaf840fe2a529f6b4adf66031ebf2393f4148671be. Mismas guardas R4 verificadas por PM antes de cerrar R4 en 07ef5558; no se aplican contra el nuevo HEAD.

Los cuatro hallazgos originales (aislamiento 110/322, cero 903 y ausencia XY114) se corrigieron y reevaluaron R2; R3 conserva 266 pruebas del principal, 53 del Revisor, 28 consultas/tres vistas del Validador en el mismo Grafana general. No se presentan como reejecuciones R4 o de este cierre. Ningún hallazgo observado de la composición queda pendiente de corrección en esos informes. La aceptación humana sigue separada.

El delta c000 contiene seis documentos/specs y cinco pruebas nuevas en un archivo. No cambia dashboards, loader, datos, métricas, despliegue, dependencias o políticas CI. Se contrastaron todas las fuentes R4, separando normalizaciones LF legítimas de cambios sustantivos. Guía y composición ya indican rúbrica mixta y datos históricos; las aclaraciones de citas/rúbrica no alteran medidas o fórmulas. Este cierre modifica sólo documentación, tareas y promoción/archivo de requisitos.

## DoD local previo y matriz aplicable

Cinco pruebas nuevas de indicadores: **5 PASS / 0 SKIP**, Python3.12 privado en Ubuntu WSL2, 0,77 s. Trazabilidad jup:check:all, OpenSpec --all --strict --no-interactive, higiene jup:cleanup:check y git diff --check: exit0 antes del archivo. Alcance, guía, continuidad, matriz y tareas reconciliados; originales preservados fuera del producto.

Los jobs/variantes leídos son OpenSpec/governance, Python azure-cost-api/backend/processor, frontend lint/test/build y typecheck, JUP policy, JUP reviews, Chat native SQL y CD con sus condiciones. CI/package/locks/herramientas de política no cambian frente a R4. Se reutilizan build y controles de política ya PASS; las suites generales conservan resultados históricos y omisiones, no se repiten por cambio documental ni se declaran verdes. La prueba nueva cubre sólo el incremento. La CI del commit final y checks remotos aún no existen en este estado sin commit; PM los comprobará tras push. Los dos títulos/reviews humanos son requisitos separados. No se repiten campañas, 266/53/38 pruebas o 28 consultas sin impacto.

## Aprobación humana posterior a evaluación

Paris autorizó el 22/10/2026 completar integración, archivar OpenSpec, commit/push y comprobar CI, mostrando la propuesta antes de abrir la PR. Esta autorización permite el archivo y los pasos indicados; no acredita lectura humana, participación o reviews de GitHub, ni dispensa sus requisitos o autoriza merge.

## Límites y siguiente paso

Lectura externa **NOT_VALIDATED** según la alternativa explícita del requisito: guion y siguiente acción humana en docs/evidence/JUP-129-validation.md. La tarea de declarar el pendiente está cumplida; la lectura no. Roles conservados: Paris líder, Lucía pairing, Alejandro revisión, Víctor validación; no se atribuye participación por asignación.

Backend: cobertura compuesta 2.577 PASS/368 SKIP sobre 2.945; 54 focales PASS, sin recuperar el marcador histórico ausente. Processor: 144 SKIP; fallos históricos y cuatro reensayos separados. Promtool cuatro PASS tras permisos de fixtures, originales FAIL preservados. No se declara el workspace verde. No se demuestra arranque completo backend/processor v4, calidad de proveedor o nuevas latencias/costes por esta composición.

Después del CLI se comprobarán promoción, enlaces y checks nativos. Candidato fijo/manifiesto al PM ANTES de reactivar a los mismos Revisor/Validador con nuevas referencias; ratificarán sólo delta/archivo. PM conserva retorno/prepublicación, enlaces permanentes, CI y pasos humanos. El archivo no cierra Trello, no es una review GitHub ni prueba de merge.


## Resultado del archivo — 22/10/2026

CLI existente `corepack pnpm openspec archive jup-129-grafana-evaluation-composition --yes --json`: exit0; archivado como `2026-10-22-jup-129-grafana-evaluation-composition`, specsUpdated=true, cuatro requisitos añadidos, cero modificados/eliminados/renombrados. Se conserva el directorio activo previo completo fuera del producto. No se omitió validación ni promoción; no hubo comandos Git. Se completó únicamente el Purpose descriptivo generado por el CLI, sin modificar requisitos/escenarios; se repararon enlaces de continuidad/evidencia al archivo. Checks posteriores y candidato fijo se entregan a PM antes de nuevas referencias y evaluadores. La lectura humana sigue NOT_VALIDATED y el archivo no demuestra aceptación completa o merge.


Comprobaciones posteriores ejecutadas: `jup:check:all`, `openspec:validate` (88 elementos PASS, cero FAIL), `jup:cleanup:check` y `git diff --check`, todos exit0. Los mismos checks previos también exit0. Se comprueba identidad exacta de los cuatro requisitos/escenarios promovidos con su delta archivado, y se revisan los enlaces locales del cierre. No se reejecutan suites o campañas; el control posarchivo no se atribuye al directorio activo ya retirado.
