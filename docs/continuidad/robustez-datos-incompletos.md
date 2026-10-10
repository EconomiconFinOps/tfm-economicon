# Robustez ante datos incompletos — JUP-071

Verificado el 10/10/2026. Origen: encargo «Implementa JUP-071 — Evaluar robustez
ante datos incompletos o ambiguos», despachado por el chat
`01a1248a-4e9e-7963-a891-5d8cb49345a6`. [Tarjeta](https://trello.com/c/H0woDubz),
ID `69da46a3e4f93822c0236e87`. No se conoce aquí el identificador del chat receptor.

## Alcance y decisión

Contribución propia en `test/JUP-071-robustness`, copia
`tfm-economicon-jup071`, base `c2995a118d419dfe725247bac9c6f219a3f0ea77` de
`origin/develop`. El checkout compartido no se cambia. No había rama ni PR propia
JUP-071 en la inspección inicial; se reutilizan JUP-069/JUP-070 ya integradas.

La [batería](../validation/JUP-071-robustness-cases.json) añade 16 variantes y
ejecuta 13 originales: 29 casos. El [runner](../../tools/assistant-robustness.py)
reutiliza prompts, transporte y comprobación numérica de JUP-070. Requeridos,
prohibiciones y conducta son juicios humanos; no se inventan ni se sustituyen por
regex. Los fallos comprobados siguen visibles aunque falten juicios. Todos los
casos de la campaña requieren dos personas, o una con `--provisional` explícito.
Los informes propios conservan sus denominadores y no se comparan como una
medición completa de JUP-067/JUP-070.

## Evidencia confirmada

- [Informe por criterio y límites](../evidence/JUP-071-validation.md).
- [Procedimiento](../validation/JUP-071-robustness.md), OpenSpec activo
  `openspec/changes/jup-071-incomplete-data-robustness/`.
- Dos ejecuciones locales del `AssistantService` real: recuperación fija y vacía
  (dobles explícitos), ambas 8 fallos numéricos/21 sin juicio semántico/0 aciertos
  entre 29 casos. No son pruebas de modelo, retrieval real ni despliegue.
- Crudos y hoja fuera de Git:
  `../materiales/07-evidencias/JUP-071-robustness-2026-10-10/` respecto al workspace
  del repositorio. Versiones y hashes en los informes; juicios vacíos conservados.
- Lectura viva del cliente desplegado en
  `DockerServer:/home/danteadmin/economicon-collaboration`: JUP-071 Backlog y
  JUP-035 Preparado; el alcance de 035 incluye conectar generación al chat. En el
  commit inspeccionado `AssistantService.answer` aún es plantilla.
- Pruebas: 38 propias, 109 JUP-070, 103 métricas y 90 Node OK; OpenSpec 56/56,
  trazabilidad e higiene correctas. `pnpm test/build` global bloqueado por fallback
  pnpm/Turbo `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`, sin corrección ajena al alcance.

## Roles, pendientes y siguiente paso

Paris mantiene liderazgo, Víctor pairing, Alejandro revisión, Lucía validación.
La aportación de código de este chat no acredita esos actos humanos ni habilita
una revisión independiente de Alejandro sobre su propia contribución. La entrega
se prepara para que Paris la integre y gestione la independencia de dictámenes;
no se reasignan roles por inferencia ni se mueve la tarjeta.

Pendiente: revisión/validación humanas e integración; después, contrastar JUP-035,
commit/modelo/prompt/corpus desplegados y realizar tres campañas reales iguales
con sus juicios. `live_unverified` conserva el límite del endpoint: no atestigua
qué modelo respondió. `generative_robustness_accepted` sigue falso. No cerrar ni
archivar la tarjeta o el chat por tener tests del instrumento verdes.
