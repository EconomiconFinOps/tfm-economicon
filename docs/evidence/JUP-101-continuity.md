# JUP-101 — Evidencia de continuidad compartida

Verificación: 2026-10-10, Europe/Paris. Entrega documental de
[JUP-101](https://trello.com/c/ReMOdXEK) en la [PR #64](https://github.com/EconomiconFinOps/tfm-economicon/pull/64).
Origen: encargo «Implementa JUP-101 — Acordar la convención compartida de
continuidad documental», delegado desde el chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`.
Esta evidencia es del implementador; no es `Validacion JUP-101` ni consenso humano.

## Versiones y límites

- Base reconciliada: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`).
- Propuesta retomada: `711f641e41f5246b704c1bb1100783da190bb2f3`, PR #64 draft.
- Candidato local del 09/10: base `ceb6520fd9b92c561c455cd8cbcd40aecf2c9f46`;
  se reutiliza su unión de tres temas, conservando además la gobernanza PR #85.
- Copia aislada: `tfm-economicon-jup101-implementation`, rama local
  `docs/JUP-101-continuity`; publicación en la rama existente de PR #64 para
  evitar otra PR. No se modifican los checkouts compartido y anterior de JUP-101.
- Git 2.56.0.windows.2, Node 24.14.1, Python 3.14.4, OpenSpec 1.8.0 y yaml 2.9.0.
  OpenSpec usa la instalación existente en modo lectura, con el directorio de
  trabajo en esta copia. No se modifica código de aplicación.

## Cobertura del alcance de la tarjeta

La tarjeta define alcance y entrega, sin checklist formal. Esta tabla traza ese
texto sin añadir criterios ni convertir pendientes humanos en aprobaciones.

| Alcance original | Evidencia de la entrega | Resultado |
| --- | --- | --- |
| Una referencia en AGENTS y un índice común | [AGENTS](../../AGENTS.md), [índice](../continuidad/README.md); comparación con la base quitando sólo el puntero | Comprobado; instrucciones de memoria y JUP-100 conservadas. |
| Conservar resúmenes, enlaces y evidencia | [Presupuestos](../continuidad/presupuestos-umbrales.md) idéntico a la base; [citas](../continuidad/citas-asistente.md) conserva íntegro el cuerpo de `711f641` tras su nota de vigencia | Comprobado documentalmente; no repite pruebas históricas. |
| Conservar la unión al integrar las PR | Unión por destino de ambos índices; tres temas, sin duplicados ni marcadores | Comprobado en esta reconciliación; no garantiza conflictos futuros. |
| Evitar duplicar el backlog | [Convención](../continuidad/convencion-compartida.md): fuentes de verdad, cortes fechados, procedimiento y plantilla | Implementado documentalmente. |
| PR documental independiente y extracción de #55 | Reutiliza PR #64 y el resumen extraído en `711f641`; sólo AGENTS, continuidad, esta evidencia y la fila de atribución en contributions difieren de la base | Comprobado; no se abre PR duplicada. |
| Acordar adaptación de #60/#61/#62 antes de sus merges | Las PR ya se integraron; se registra debajo el hecho y se corrige la referencia histórica | Acuerdo previo no acreditado; no se inventa retrospectivamente. |
| No atribuir aprobaciones ni eliminar trabajo ajeno | Conformidad de Paris enlazada; roles históricos propuestos y excepción de cierre explícitos; preservación del tema ajeno | Comprobado; no se acredita consenso ni reviews independientes. |

## Fuentes consultadas de nuevo

Trello: 2026-10-10 09:21 Europe/Paris, mediante `TrelloClient` de la integración
desplegada en `DockerServer:/home/danteadmin/economicon-collaboration`, ejecutada
con `docker compose run --rm -T --entrypoint python collaboration -`.
Tarjeta `6abf7caff38b77c0c18c1b5f`: `10 — Backlog`, sin etiquetas, fecha ni miembros;
descripción intacta con roles propuestos y aceptación pendiente. No aparecieron
acciones de esta tarjeta entre las últimas 100 del tablero; no es una lectura
completa de su historial. No se consultó otro acceso a Trello.

GitHub: leídas todas las reviews, comentarios de conversación e inline de PR #64;
head `711f641`, cero reviews, cero inline y una conformidad de
[Paris](https://github.com/EconomiconFinOps/tfm-economicon/pull/64#issuecomment-5974860953).
Se consultaron las PR relacionadas: sus merges son hechos, no evidencia de que
el equipo acordase JUP-101 antes de integrarlas.

| PR | Merge verificado (Europe/Paris) | Commit |
| --- | --- | --- |
| [#55 — citas](https://github.com/EconomiconFinOps/tfm-economicon/pull/55) | 2026-10-07 23:48 | `193cf6c692077d4ddf78453764464f4f84873765` |
| [#60 — decisiones](https://github.com/EconomiconFinOps/tfm-economicon/pull/60) | 2026-10-04 16:32 | `d61e63111f837e776c3614f5a64c8b7ac562d981` |
| [#61 — presupuestos](https://github.com/EconomiconFinOps/tfm-economicon/pull/61) | 2026-10-08 02:24 | `8cc5db0b8f96b7289f9b90dfed42527b76d0222d` |
| [#62 — anomalías](https://github.com/EconomiconFinOps/tfm-economicon/pull/62) | 2026-10-04 02:55 | `dad56626d2c6e3314c1de8aaeb6c583895c422f3` |
| [#85 — memoria](https://github.com/EconomiconFinOps/tfm-economicon/pull/85) | 2026-10-10 08:56 | `c2995a118d419dfe725247bac9c6f219a3f0ea77` |

## Verificaciones reproducibles

Desde la raíz del repositorio, con las dependencias declaradas disponibles
(`corepack pnpm install --frozen-lockfile` en una copia nueva):

```powershell
git diff --check
node tools/jup-check.mjs --all
node tools/jup-cleanup-check.mjs
node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs
corepack pnpm openspec:validate
```

Se ejecuta el binario OpenSpec 1.8.0 ya instalado con los mismos argumentos
`validate --all --strict --no-interactive`. La primera ejecución de higiene y
tests fue impedida por `spawn EPERM` del sandbox; se repite con permisos para
subprocesos, sin modificar los controles.

El control de CI necesitaba `yaml` en la copia aislada: se copió únicamente el
paquete 2.9.0 ya instalado a su `node_modules` ignorado y se repitió ese control.

| Comprobación | Resultado local |
| --- | --- |
| `git diff --check` y `git diff --cached --check` | Sin errores. |
| `node tools/jup-check.mjs --all` | 8 cambios enlazados y completos. |
| `node tools/jup-cleanup-check.mjs` | 976 archivos sin infracciones. |
| Política PR y gobernanza | 70 pruebas aprobadas. |
| CI workflow, tras proporcionar yaml | 12 pruebas aprobadas. Total final de las tres suites: 82 aprobadas. |
| OpenSpec estricto | 55 elementos aprobados, 0 fallos. |
| Preservación y enlaces | Unión exacta de 3 temas; 18 enlaces relativos resueltos; 0 marcadores de conflicto; presupuestos, cuerpo histórico de citas y resto de AGENTS preservados. |

No se han ejecutado pruebas de aplicación, builds,
integraciones funcionales ni nuevas pruebas de citas o presupuestos: el delta es
documental. CI remoto se consulta separadamente tras publicar el head.

La comprobación documental compara los conjuntos de destinos de los índices,
el texto completo de presupuestos con la base, el cuerpo histórico de citas con
la propuesta, AGENTS menos su único puntero con la base, y resuelve enlaces
relativos de los seis documentos afectados o preservados. No valida la semántica
de todas las URLs externas ni sustituye una revisión humana.

Los snapshots de fuente, el script puntual `check-docs.py` y su manifiesto de
SHA-256 se conservan en el espacio de coordinación, fuera del repositorio:
`materiales/07-evidencias/JUP-101-implementacion-2026-10-10/`.
Para repetir allí la comprobación: `python check-docs.py`. El script fija los
dos commits anteriores y la copia aislada. En otra copia se ajusta sólo su raíz.
La preservación del tema ajeno también se comprueba con
`git diff c2995a118d419dfe725247bac9c6f219a3f0ea77 -- docs/continuidad/presupuestos-umbrales.md`
(salida vacía); `git diff 711f641 -- docs/continuidad/citas-asistente.md` debe
mostrar sólo la nota de vigencia añadida.

## Excepción de atribución y cierre por plazo del MVP

El 2026-10-10 el usuario instruyó en este chat: «Estamos fuera de fecha, completa
todas las tareas necesarias marcando en la atribucion la excepcion por estar
fuera de plazo para la entrega del MVP». Esta autorización posterior sustituye
para **JUP-101** la espera de acuerdo/roles/reviews y habilita el cierre excepcional
por PR #64. No convierte esos actos humanos en hechos ocurridos ni modifica
permanentemente CONTRIBUTING, el checker o las reglas de protección.

| Participante / medio | Atribución real | Requisito humano dispensado para este cierre |
| --- | --- | --- |
| Alejandro Aguado (`Iber1to`), con ejecución asistida por Codex | Implementación y comprobación técnica mediante su cuenta, por encargo del usuario; integración prevista por esa vía tras verificar CI final | No se presenta la autocomprobación como review independiente. |
| Paris Arcos Martin | Conformidad sobre la convención del 04/10, enlazada arriba | Pairing no acreditado; no se inventa coautoría. |
| Lucia Mateo | Revisora propuesta históricamente | `Revision JUP-101` independiente no realizada ni atribuida; dispensada. |
| Victor Mendez | Validador propuesto históricamente | `Validacion JUP-101` independiente no realizada ni atribuida; dispensada. |
| Usuario | Instrucción expresa de completar y registrar la excepción por plazo | Adopción excepcional para el MVP; no equivale a consenso de todo el equipo. |

Se verificó de nuevo el ruleset activo `21475971`: permite a administradores
(`RepositoryRole`, `actor_id: 5`) bypass sólo en `pull_request`. La cuenta conectada
es `Iber1to` y tiene permiso admin. Se usará esa facultad ya configurada en la
PR existente; no se eliminan checks, no se simula su éxito y no se hace push
directo a develop. La línea de excepción de «revisión y validación por la misma
persona» no se aplica: no describe lo ocurrido.

El head previo `c58616c` pasó los siete trabajos técnicos de
[CI](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38034739888).
Sobre el delta de excepción se vuelven a comprobar preservación/enlaces e higiene;
el head final debe completar su CI técnico antes de integrar. La ausencia de
reviews y el bypass se mantienen explícitos en PR y Trello; no se acreditan
pruebas funcionales humanas mediante esta nota.

Recomprobación local del delta: tres temas conservados, 24 enlaces relativos
resueltos en siete documentos, presupuestos/cuerpo histórico de citas/AGENTS
preservados, diff sin errores e higiene de 976 archivos correcta. La descripción
de PR pasa el checker de metadatos; esto no acredita ejecución de los roles
históricos propuestos. El manifiesto `exception-documentation-check.json`
acompaña al script `check-exception.py` en el directorio de evidencias local.
El sandbox volvió a impedir el subproceso Git del control de higiene; la
repetición autorizada fuera del sandbox pasó sin modificar código ni controles.

Secuencia de cierre: registrar excepción y atribución en PR/Trello, publicar
el delta documental, verificar CI final, integrar PR #64 por squash con head
fijado y, tras comprobar el merge, pasar JUP-101 a Hecho. El recibo final con SHA,
CI y acción Trello se guarda junto a las fuentes del espacio de coordinación.
La condición de fuera de plazo procede del usuario: la tarjeta no tenía `due`,
y no se inventa uno ni se cambia prioridad. Las revisiones humanas omitidas
permanecen identificadas como dispensadas, no como trabajo futuro necesario para
este cierre excepcional.
