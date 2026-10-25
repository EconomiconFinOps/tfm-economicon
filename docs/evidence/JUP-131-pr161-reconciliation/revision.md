Revision JUP-131

**Veredicto: APPROVE.** Revisión técnica independiente del candidato inmutable `812697387918c25e905a240fa35573091d9fdc16`. No quedan hallazgos P0/P1/P2 abiertos en el delta revisado. La ambigüedad de roles detectada en `bfffb88b0086f1a255dc8098f22a3240d21e3880` se corrigió en 964c9f55 y se revalidó; el candidato final conserva esa corrección.

Autor real: agente Codex `/root/pr161_code_review`, bajo la excepción expresamente autorizada por el usuario para PR161. Fecha: 25/10/2026, Europe/Paris. No se atribuye este dictamen a Lucía Mateo ni a otro miembro humano, y no es una review publicada mediante la API de GitHub. PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/161. Origen: «Preparar despliegue en AWS», chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`.

- Base anterior revisada: `30d4370aca3903cf764111e451153ae2ed83510c`.
- Base de aplicación aprobada por el usuario: `0edd11eff3458683553bd4c36f3011b77c1d3de4`.
- Cortes intermedios inspeccionados: `da13f069c0f92258bb2856ff33b204cc3b176e89`, `bfffb88b0086f1a255dc8098f22a3240d21e3880`, `964c9f5516402e9425be1ec5556bd485c8c94db8` y `3062c80b3ace02c084a5a30cc6fa1be633dcd8f2`.
- Candidato final revisado: `812697387918c25e905a240fa35573091d9fdc16`, rama `feat/JUP-131-atlas-ecs`.

### Ámbito y conclusiones

Se leyeron AGENTS, CONTRIBUTING, el índice de continuidad, el inicio pertinente de `cloud-aws.md` y el plan `docs/planning/2026-10-25-jup131-reconcile-master.md`. Se revisó el diff desde la base anterior, los dos arreglos posteriores del reconocedor de evidencia y el contexto completo del checker, workflow, controlador y preparación. Se siguieron los consumidores de la configuración y los controles de aceptación/CI/caducidad del runner.

**Reconciliación de aplicación.** La base aprobada 0edd es ancestro del candidato. `errors.py`, requisitos y pruebas de Azure, y todo `apps/landing/`, son idénticos a esa base en el candidato final. Se conserva `starlette==1.9.0`; el cambio anterior de `ApiError` mutable y su test se retiran conforme a la instrucción del usuario. El dictamen Azure del 24/10 queda como histórico, no como una corrección que deba reintroducirse. La reconciliación no altera el SQL Atlas ni los archivos de infraestructura de monitorización previamente revisados, incluido el bloqueo de métricas del ALB.

**Excepción PR161.** `tools/pr161-agent-evidence.mjs` exige número, repositorio, autor, rama/base, primer identificador del título, una declaración visible y los cuatro roles canónicos. Comprueba un checkout igual al head leído en vivo, usa `git show` sobre ese head para leer los registros, verifica sus hashes normalizando CRLF, exige agentes/veredictos/títulos/candidato previstos y verifica la integridad de ambos Markdown. El candidato debe ser ancestro; el diff posterior sólo puede afectar a los diez paths documentales enumerados explícitamente. La evidencia ausente, ilegible, negativa o fuera de alcance produce errores, sin activar la excepción.

El workflow obtiene el SHA del evento y el historial Git completo. El checker lee el head vigente de GitHub: un evento obsoleto no puede acreditar otro checkout. `checkReviews` sólo omite la falta de títulos humanos cuando la excepción está activa; conserva la resolución histórica de solicitudes de cambios y las reglas generales. Un Comment posterior no levanta un Request changes. Otras PR sin esta declaración mantienen el flujo anterior.

Estos registros comprueban coherencia e integridad de la evidencia publicada; no autentican criptográficamente la identidad de los agentes ni sustituyen al coordinador que publica los informes reales. Esta limitación está declarada en CONTRIBUTING y no se interpreta como una review humana ni como permiso de merge.

**Presupuesto.** La retirada del requisito sólo se activa con cuenta `323188184300` y política exacta `master-account-authorized-2026-10-24`. Exige omitir `budget_eur` y `available_credit_eur`, y mantiene una estimación finita y positiva. Otra cuenta o política no obtiene la excepción. Las otras configuraciones conservan el límite y la comprobación de saldo anteriores. No se hallaron consumidores productivos adicionales que accedan a los campos ahora omitidos.

El waiver no modifica el SHA de fuente, las regiones, la identidad real de cuenta comprobada en el runner, los hashes de aceptación, las cuotas, la vinculación del plan/configuración ni la autorización. La validación del runner sigue exigiendo caducidad dentro de ocho horas y CI `push` completada con éxito, para el SHA exacto en `develop`, más su ancestry. La preparación describe el límite organizativo como no verificado; no inventa saldo ni límites de Pontia.

**Actualización de aceptación offline.** El único delta entre 964c9f55 y el candidato final afecta a `infra/aws-cicd/release.json` y al nuevo recibo `docs/evidence/JUP-131-pr161-reconciliation/application-acceptance.md`. Se verificaron independientemente los 851 archivos de aplicación versionados del candidato mediante blobs Git, reproduciendo las exclusiones y el orden de `application_digest`: la huella es `5e19f3f4ff0db6039ebc42b2733d9dd4266e94b55c6fc8fac741c21876461e70`, exactamente la declarada por la receta. `apps/` no cambia entre el candidato CI da13 y 81269738.

Se conservan intactas las cinco entradas históricas y se añade la sexta evidencia `reconciliation`. Los seis hashes de evidencia coinciden con sus archivos del candidato. El recibo nuevo tiene SHA256 normalizado `5eb418403fcf3dcc0dbccde23c7423e38f138da2cb2b206eee400f4afa87a3f0`. No cambian los comandos, entornos ni modelos de la receta. El digest cubre `apps/`, no Terraform/ECS, que se revisan mediante el SHA y sus pruebas. El recibo distingue CI y contenedores desechables de runtime AWS, inferencias e imágenes finales; no interpreta los informes históricos como pruebas nuevas. Esta renovación offline no concede `application_ready`, autorización de arranque ni CI válida de `develop`.

### Hallazgo conservado y cerrado

**P2 — Rechazar roles visibles duplicados aunque cambien las mayúsculas.** En `bfffb88b`, `tools/pr161-agent-evidence.mjs:38` contaba etiquetas mediante `startsWith` sensible a mayúsculas, mientras `readRole` en `tools/pr-policy.mjs:23` las reconocía sin distinguirlas. Anteponer esta línea a la asignación canónica del agente producía dos roles contradictorios:

```text
- revision de pr: Paris Arcos Martin
- Revision de PR: Agente pr161_code_review (excepcion PR161)
```

Con un manifiesto sintético íntegro, tanto `checkReviews` como `checkPullRequest` devolvían `[]`. Se reprodujo también con `pairing/coautoria`: el resultado propio fue **13 PASS / 2 FAIL** sobre bfffb88b. Esto permitía dar por válida la asignación puntual sin cumplir la unicidad de roles requerida. Se pidió contar etiquetas de forma consistente antes de exigir el valor canónico.

**Cierre en 964c9f55.** El conteo ahora normaliza mayúsculas/minúsculas y los tests del repositorio cubren duplicados de los cuatro roles. El mismo candidato endurece los ID duplicados con espacios, alineándolos con el parser general. La prueba propia final comprueba los cuatro roles, el ID y el título con otro JUP: **18 PASS / 0 FAIL**. Se conserva sin editar la evidencia RED propia en `.work/pr161-reconciliation-review/adversarial-evidence-bfffb88b.json` y su helper `.mjs`. El defecto del primer ID del título, identificado y corregido por el coordinador en bfffb88b, también fue revalidado con resultado negativo correcto.

### Comprobaciones ejecutadas por este revisor

1. Identidad de HEAD, ancestry de 0edd, revisión de diffs y `git diff --check` desde 30d4370a hasta 81269738: PASS. Comparación por Git de Azure y landing contra 0edd: sin diferencias. El blob de `ApiError` coincide: `a5ff184e4729d2248a3ff12c3001f3076f2ccdff`. Al cerrar, sólo había cambios documentales locales del coordinador dentro de la allowlist; no se incluyen como parte del SHA revisado.
2. `node .work/pr161-reconciliation-review/adversarial-evidence.mjs`: **18 PASS**, sin fallos, ejecutados sobre 964c9f55. Los archivos de política y workflow son idénticos en 81269738; no se atribuye una segunda ejecución. Incluye ámbito correcto/incorrecto, título, roles/ID duplicados, declaración oculta, checkout obsoleto, solicitudes de cambios, Comment que no las resuelve, aprobación que sí las resuelve, publicación documental permitida, código posterior rechazado y hash de Markdown alterado. Usa informes y repositorios Git sintéticos dentro de la carpeta propia; no lee el informe real del validador. Resultado persistente: `.work/pr161-reconciliation-review/adversarial-evidence-964c9f55.json`.
3. Seis tests focales de unittest desde `tools/aws_demo`, con Python `-B`: **6 PASS**. Cubren autorización del máster sin saldo inventado, rechazo de otra cuenta/política, conservación de SHA/formato de expiración/regiones/estimación, SHA obsoleto, aprobación expirada y plan obsoleto antes de Terraform. Los dos tests del runner usan dobles y no inicializan servicios ni clientes cloud.
4. `python -B .work/pr161-reconciliation-review/acceptance-audit.py`: **PASS** sobre 81269738. Compara digest de 851 blobs de aplicación, seis hashes de evidencia, las cinco entradas históricas conservadas y el resto de la receta sin cambios; sólo lee objetos Git versionados. Evidencia: `.work/pr161-reconciliation-review/acceptance-audit.json`.
5. `python -B -m unittest test_release_readiness.ReleaseReadinessTests -v`, desde `tools/aws_demo`: **5 PASS** sobre 81269738. Se comprueba rechazo de deriva de aplicación, evidencia alterada/ausente/fuera de raíz y scripts ausentes/inválidos, así como el bloqueo antes de operaciones cloud. Los fixtures se limitaron al directorio temporal propio.

El primer intento del harness Node fue bloqueado por el sandbox (`spawnSync git EPERM`); se repitió con permiso de ejecución local sobre el mismo fixture aislado. El primer comando de unittest utilizó el directorio de importación incorrecto: cuatro errores de carga y dos pases; al usar `tools/aws_demo` se obtuvieron los seis pases indicados. El primer intento de los cinco tests de readiness tuvo errores de permisos al crear/limpiar los temporales del sandbox; la repetición local autorizada sobre otro temporal propio obtuvo los cinco pases. Ninguno de esos fallos de invocación se atribuye al producto ni se cuenta como validación superada.

El coordinador aportó `.work/pr161-reconciliation/policy-green.log`; se leyó su cierre **111 PASS / 0 FAIL**. Esa batería no fue ejecutada por este revisor. No se reutilizaron los resultados de otros agentes como comprobaciones propias.

### Límites y pasos pendientes

No se ejecutaron Docker, Terraform, suites extensas de aplicación, HTTP, SQL, AWS, inferencias, builds cloud o despliegues por este revisor. No se leyeron credenciales, `.aws`, archivos privados ni el informe del validador. No se hicieron commits en el proyecto, push, publicaciones o cambios tracked; sólo se escribieron artefactos propios y commits de fixtures desechables.

No se consultó GitHub desde este agente. El coordinador y el recibo leído informan SUCCESS de CI `40187165537`/`40187163124` y SQL `40187165282` sobre **da13**, que conserva el mismo árbol de aplicaciones. Esos resultados no se atribuyen al head 81269738 ni a una ejecución propia. Deben completarse la CI del head que se publique, el dictamen independiente de validación y la publicación íntegra de ambos informes. Cualquier nuevo delta de código requiere revalidación; la publicación documental debe respetar la allowlist.

La preparación de la cuenta máster, su ventana, aceptación del conjunto y CI exacta de `develop` siguen siendo gates operativos separados. No se acredita saldo, cuota actual, aceptación renovada, permiso de merge ni permiso para iniciar el ensayo AWS. Los informes originales del 24/10 permanecen históricos y sin modificaciones.
