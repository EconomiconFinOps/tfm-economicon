# Corrección de CI — JUP-131 — 23/10/2026

Solicitud humana en HAL9000: resolver CI que bloquea PR154/JUP-138. Base de la
corrección: develop `84b53b74d02ff5831ef9dbdd4f9c7d8c40cd4d24`.
Se leyeron las cuatro reviews, dos comentarios y ningún comentario inline de
[PR154](https://github.com/EconomiconFinOps/tfm-economicon/pull/154).
JUP-131 y sus roles se contrastaron mediante el puente oficial de DockerServer;
las asignaciones no acreditan pairing ni dictámenes realizados.

## Diagnóstico

- [Processor120482908761](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39958058542/job/120482908761):
  instalación desde14:55:46UTC hasta cancelación15:15:36UTC; varios `Ign:` en
  azure.archive.ubuntu.com, incluido LibreOffice24.2.7. No consta un error final
  que pruebe desincronización del mirror. El processor del push
  [120475464424](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39958050200/job/120475464424)
  pasó en otro intento; no es evidencia de tests fallidos por producto.
- [AWS offline120475393489](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/39958050200/job/120475393489):
  `test_versioned_release_matches_application_and_acceptance_evidence` falla con
  `Release evidence application tree differs`. Reproducido en la base:69casos,
  un error y una omisión. La prueba confundía integridad de evidencia versionada
  con aceptación para desplegar todos los cambios posteriores de `apps/`.

## Corrección y límites

`validate_recipe_evidence` verifica huellas y existencia de las evidencias,
confinamiento de rutas y scripts Python. CI usa esa comprobación de integridad.
`validate_recipe_files` conserva la comparación exacta de la aplicación y llama
después a la misma comprobación; prepare y runner continúan usando esta guarda.
No se modifica `release.json`, sus evidencias, el digest aceptado ni `apps/`.
La CI del controlador no concede aceptación AWS a una aplicación nueva.

APT dispone de cinco reintentos y esperas HTTP/HTTPS de30s tanto en update como
en install. El paso completo tiene ocho minutos; sigue fallando si no instala
las herramientas necesarias, sin `continue-on-error` ni omisión de tests.

## Validación local

- Regresión escrita antes de extraer la función: fallos por API inexistente;
  después74casos,73PASS/1SKIP con `python -m unittest discover -s tools/aws_demo
  -p 'test_*.py' -v`. La omisión requiere PostgreSQL opt-in, no se cuenta como PASS.
- Cinco casos nuevos: evidencia íntegra con aplicación cambiada pero despliegue
  rechazado; evidencia alterada/ausente/fuera de raíz; scripts ausentes/inválidos;
  prepare con readinessfalse; runner rechazando antes de llamadas cloud.
- `python tools/aws_demo/prepare.py --allow-incomplete` genera un informe
  bloqueado, incluido el digest distinto; ningún recurso AWS ni preflight cloud.
- `node --test tools/ci-workflow.test.mjs tools/pr-policy.test.mjs`:123PASS.
  Primer intento bloqueado por `spawn EPERM` del sandbox; ejecución posterior
  con permiso de proceso conforme, sin alterar las pruebas.
- OpenSpec estricto:92PASS; trazabilidad JUP-131, higiene y `git diff --check`
  conformes. No se ejecutaron nuevas campañas generativas ni servicios locales.

Pendientes al redactar: CI del commit publicado y reviews de esta corrección.
No se atribuye aceptación funcional, pairing humano, merge ni despliegue.
