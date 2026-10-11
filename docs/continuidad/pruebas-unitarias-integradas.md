# Pruebas unitarias e integradas — JUP-054

Verificación: 2026-10-10. Encargo: «Implementa JUP-054 — Implementar pruebas
unitarias e integradas»; chat de origen del encargo:
`01a1248a-4e9e-7963-a891-5d8cb49345a6`. ID del chat ejecutor no proporcionado.

## Confirmado y decisiones

- [Trello](https://trello.com/c/ZsxwmagI) contrastado por integración oficial
  `DockerServer:/home/danteadmin/economicon-collaboration`; mismo alcance que
  `materiales/07-evidencias/hito-mvp-2026-10-09/backlog-dispatch-source.json`
  del workspace coordinador.
- Base `origin/develop` `c2995a1`; sin rama/PR previa JUP-054 encontrada.
  Copia aislada `tfm-economicon-jup054`, rama `test/JUP-054-critical-flows`.
- Las 194 pruebas y los 49 errores de lint de agosto son históricos. Se reutiliza
  JUP-087 y la cobertura de auth/tenant/RAG ya integrada; se añaden sólo los
  límites Azure productor/consumidor, agente/pipeline y lectura JSONB/historial.
- [Matriz y comandos](../testing/critical-flows.md),
  [evidencia por criterio](../evidence/JUP-054-validation.md),
  [OpenSpec archivado](../../openspec/changes/archive/2026-10-10-jup-054-test-strategy-and-critical-flows/proposal.md).
- Vitest directo en el job CI existente; no cambia nombres de checks ni reglas
  de protección. Las integraciones reales de CI siguen opt-in.
- Asignaciones nominales iniciales: Lucia liderazgo, Paris pairing, Victor
  revisión, Alejandro validación. No prueban participación efectiva. Para este
  cierre excepcional, la ejecución, pruebas, documentación e integración se
  atribuyen a Alejandro (`Iber1to`), con asistencia de Codex; no se acredita
  pairing ni dictámenes humanos independientes.

## Entrega y excepción por plazo del MVP

[PR #93](https://github.com/EconomiconFinOps/tfm-economicon/pull/93): 7 pruebas
nuevas, CI Linux 2041 passed / 91 skipped y recorrido real 3 passed. Windows
presenta limitaciones de socketpair y tiempos, conservadas en el informe.

El 10/10/2026 el usuario autorizó expresamente: «Estamos fuera de fecha, completa
todas las tareas necesarias marcando en la atribucion la excepcion por estar
fuera de plazo para la entrega del MVP». Esta instrucción sustituye, para JUP-054,
la espera de adopción/reviews descrita en la entrega inicial. No modifica el flujo
general del equipo ni supone una aprobación humana independiente.

Se aplica la [excepción administrativa mediante PR](../governance/github-branch-protection.md#administrator-exception-and-teammate-onboarding)
existente para el cierre fuera de plazo. Permiso admin de `Iber1to` y bypass
`pull_request` de la regla `21475971` confirmados el 10/10. No se modifican
protecciones ni se presenta `JUP reviews` como aprobado. Los siete controles
técnicos deben pasar sobre el último commit antes de integrar. Revisión final
asistida Codex sin hallazgos; incluye autorrevisión de las aserciones de historial,
por lo que no se acredita independencia humana.

OpenSpec archivado el 10/10 con tres requisitos publicados en
`openspec/specs/critical-flow-testing/spec.md`. Atribución excepcional registrada
en [contribuciones](../contributions/README.md#excepción-de-entrega-del-mvp--jup-054).
El evento de merge de la PR y el comentario de cierre en
[Trello](https://trello.com/c/ZsxwmagI) son las fuentes del resultado administrativo.

El comentario inicial `6ac9ee125de4e83652da6c32` conserva el estado histórico
anterior a esta autorización: Backlog y draft. Queda superado por la excepción
de este apartado. Los contenedores/red/túnel exclusivos ya se retiraron.
Repetición final conjunta: 7 passed en 24.53 s. Sin mensajes Discord.

Reconciliación del 10/10 con `develop` `d7c0725` (JUP-102 / PR #108): se
conservaron ambos temas y atribuciones. Revalidación por dependencia vectorial:
los 3 recorridos reales y un caso real de inicialización JUP-102 pasaron juntos
en 13.23 s, sin skips. Evidencia y recibo de retirada de servicios propios en
`.artifacts/jup054/linux-reconciled-*` y `reconciled-cleanup.txt`. El CI final de
la PR cubre la base reconciliada; 2041/91 son los conteos de la base inicial.

## Límites conservados

La entrega no certifica Azure cloud, LLM externo, gateway LiteLLM real, reinicio
RabbitMQ, todas las migraciones, Compose completo ni navegador real. RF-096-004
(infraestructura en CI) sigue separado. Estos límites no se borran con la excepción.


## Segunda pasada: cobertura del candidato final

Verificación: 2026-10-10. Rama `test/JUP-054-final-candidate-coverage`, OpenSpec
[`jup-054-final-candidate-coverage`](../../openspec/changes/jup-054-final-candidate-coverage/proposal.md)
(al archivarse hay que actualizar este enlace a su ruta en `archive/`). La
tarjeta deja pendiente comprobar la cobertura del candidato final y cubrir los
huecos; la PR #93 no se rehace ni se duplica.

- **Candidato auditado:** `develop` en `e1c2a8f`, que ya incluye cinco PR
  posteriores a la #93. Referencia de CI sobre ese SHA: ejecución `38079384876`,
  2135 pruebas aprobadas y 127 omitidas. `develop` no había avanzado al cerrar la
  pasada.
- **Medición:** diagnóstico sin umbral y fuera del repositorio (herramienta sólo
  en contenedores Linux desechables). Cada cifra vale porque la ejecución
  instrumentada reproduce a CI. Comandos en la
  [matriz](../testing/critical-flows.md#medición-de-cobertura-diagnóstico).
- **Resultado:** 291 pruebas nuevas en nueve archivos, sin ningún cambio de
  producto ni de dependencias, y sin añadir omitidas. Cobertura combinada
  antes → después: azure-cost-api 94,4 % → 95,1 %, backend 85,0 % → 85,6 % y
  processor 86,3 % → 88,6 %; el frontend no cambia. Detalle por hueco, supervivientes
  y límites en la [evidencia](../evidence/JUP-054-validation.md#segunda-pasada-cobertura-del-candidato-final).
- **Defectos de producto detectados y no corregidos**, sin fijarlos con pruebas:
  un `result` persistido corrupto que deja un mensaje reentregándose sin fin
  (`RF-054-001`), una clave larga que esquiva la redacción de metadatos sensibles
  (`RF-054-002`), excepciones de red sin mapear que impiden al CLI emitir su JSON de
  fallo (`RF-054-004`), una rama inalcanzable (`RF-054-003`) y una ambigüedad de
  contrato sobre mayúsculas (`RF-054-005`). Los huecos diferidos y los supervivientes
  están en `RF-054-006` a `RF-054-009`.
- **Lo que sigue sin acreditarse:** la ejecución de CI de esta PR, el SQL real que
  sólo corre con CockroachDB, pgvector y RabbitMQ (127 omitidas; `RF-096-004` no se
  amplía), la semántica de `rowcount` de CockroachDB, el frontend nuevo y Windows.
- **Revisión:** sigue el flujo ordinario de `CONTRIBUTING.md`; la excepción de
  plazo del MVP de la primera pasada no se extiende a esta rama. Los veredictos de
  QA y los informes del tester son de agentes de apoyo, no una revisión humana
  independiente. Quién revisa y quién valida lo decide el equipo en Trello.
- **Siguiente acción:** abrir la PR contra `develop`, enlazar su CI en la evidencia
  y, si el equipo lo prioriza, corregir los defectos (cada uno con su prueba de
  regresión) o aclarar el contrato de `RF-054-005`.
