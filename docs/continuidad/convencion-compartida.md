# Convención compartida de continuidad

Verificación documental: **2026-10-10**. Origen: [JUP-101](https://trello.com/c/ReMOdXEK)
y [PR #64](https://github.com/EconomiconFinOps/tfm-economicon/pull/64), a partir de
la [observación de Víctor en JUP-025](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5385253656).
Estado: **adopción para el MVP por excepción de plazo autorizada por el usuario**.
El 10/10 el usuario ordenó completar las tareas necesarias y marcar en la
atribución la excepción por estar fuera de plazo para entregar el MVP. Esta
decisión permite completar JUP-101 mediante la PR existente; no acredita consenso,
pairing ni aprobaciones del equipo. El estado de integración está en PR #64 y
la tarjeta, y su atribución en la [evidencia de cierre](../evidence/JUP-101-continuity.md#excepción-de-atribución-y-cierre-por-plazo-del-mvp).

## Alcance y fuentes de verdad

Un solo índice `docs/continuidad/README.md` y una sola referencia a él desde
`AGENTS.md`, dentro de la raíz real del proyecto. Cada tema tiene un archivo
estable y descriptivo, por ejemplo `presupuestos-umbrales.md`; se actualiza el
existente en lugar de crear uno por conversación. En espacios con varios
proyectos, la continuidad de cada proyecto permanece en su propio directorio.

| Fuente | Responsabilidad | Qué enlaza la continuidad |
| --- | --- | --- |
| Trello | Alcance, prioridad, responsables, fechas y estado operativo | Tarjeta JUP y decisiones atribuibles; las copias de estado llevan fecha de consulta. |
| GitHub | Código, documentación, PR, reviews y evidencia de integración | PR, revisión y commit concreto que respaldan una conclusión. |
| OpenSpec | Requisitos, diseño y escenarios técnicos versionados | Cambio o especificación pertinente; enlace actualizado tras su archivo. |
| Continuidad | Contexto mínimo para retomar el trabajo y entender decisiones | Problema, evidencia, límites y siguiente acción; no un backlog paralelo. |

La memoria final del TFM sigue su [gobernanza propia](../memoria/README.md).
Estos resúmenes no copian la memoria ni reemplazan ADR, informes o registros existentes.

## Qué guardar y cuándo

1. Al empezar, leer las instrucciones del proyecto, el índice y únicamente los
   temas pertinentes. Crear directorio e índice si aún no existen.
2. Antes de editar un tema, leer su versión actual y reconciliar aportaciones
   posteriores. Mantener problema y alcance, decisiones y motivos, evidencias,
   comandos reproducibles, archivos, dudas abiertas y siguientes pasos concretos.
3. Separar hechos confirmados, hipótesis y comprobaciones pendientes. Fechar cada
   verificación; conservar las fechas de pruebas anteriores y señalar lo superado.
   Registrar título e identificador del encargo cuando se conozcan, sin inventarlos.
4. Actualizar tema e índice después de hitos relevantes y antes de concluir o de
   un archivo de tarea solicitado. El índice lleva enlace relativo, descripción,
   estado documental breve y fecha de actualización. No depende de detectar un
   archivo manual de la conversación.
5. Enlazar informes, scripts y fuentes originales en vez de transcribirlos.
   Preferir rutas relativas dentro del proyecto y permalinks a commits para
   evidencia histórica; al mover un documento, reparar los enlaces afectados.
6. No guardar contraseñas, tokens, claves, cookies ni credenciales. Reducir los
   datos personales al mínimo necesario para atribuir decisiones y roles.

Plantilla orientativa para un tema, sin introducir campos de backlog propios:

```markdown
# Tema descriptivo
Verificado: AAAA-MM-DD. Origen: título/ID del encargo, tarjeta y PR si existen.
Estado documental: propuesta, evidencia histórica o conclusión confirmada.

## Problema y alcance
## Hechos, decisiones y motivos
## Evidencia y reproducción
Fuentes, revisión/commit, comandos, fecha, resultados y limitaciones.
## Hipótesis y pendientes
## Siguientes pasos
Acción concreta y dependencia o responsable sólo cuando estén confirmados.
```

## Cómo reconciliar ramas

1. Leer `CONTRIBUTING.md` y el estado de la PR. Actualizar la base en la rama de
   trabajo autorizada; quien revisa o valida no publica commits en la rama ajena.
2. Comparar los índices de ambos lados. Conservar la **unión de temas por destino**,
   manteniendo sus archivos y enlaces. Si un destino aparece en ambos, revisar
   ambos contenidos y reconciliar semánticamente; una fecha posterior por sí
   sola no justifica descartar evidencia anterior ni confirmar un pendiente.
3. Conservar los temas ajenos sin reescribir sus conclusiones. Distinguir un
   corte histórico de una consulta nueva. No importar notas locales de otras
   conversaciones como si estuvieran ya versionadas en la base.
4. Mantener una sola referencia al índice en `AGENTS.md`, sin eliminar otras
   instrucciones. Evitar resolver todo con `ours`/`theirs`.
5. Comprobar que todos los destinos relativos existen, que no quedan marcadores
   de conflicto y que la evidencia previa se conserva. Ejecutar `git diff --check`
   y los controles aplicables del repositorio. Registrar base, head, comandos y límites.
6. Publicar el resultado en la PR y aplicar las revisiones y validación de
   [CONTRIBUTING.md](../../CONTRIBUTING.md#review-and-validation-flow). Una unión
   técnicamente correcta no sustituye el acuerdo humano ni autoriza el merge.

## Reconciliación de esta entrega

La propuesta original `711f641e41f5246b704c1bb1100783da190bb2f3` se retoma
desde `develop` `c2995a118d419dfe725247bac9c6f219a3f0ea77`. El candidato local del
09/10 se usa como referencia de preservación, no como base actual: precede la
gobernanza de memoria incorporada por PR #85.

La primera reconciliación resolvió el conflicto del índice conservando tres temas:
presupuestos JUP-029, citas JUP-025 y convención JUP-101. El resumen y la fila
histórica de presupuestos se conservan; citas mantiene todo su texto y evidencia
de 01–02/10, con una nota separada de vigencia. AGENTS conserva la regla de memoria
externa y el proceso de reviews JUP-100 de la base actual.

Antes del cierre, PR #108 incorporó JUP-102 a develop
`d7c07255c51ad9484971ddcdff42e0a8cf7dc994`. Se incorporan su fila y tema de dimensión
vectorial sin alterarlos: el índice resultante tiene **cuatro temas**. Se conserva
el único puntero de AGENTS ya integrado por esa PR y se retira la adición equivalente
de esta rama, evitando duplicarlo. La nueva entrada de atribución de JUP-102 y
todos sus cambios técnicos se conservan; JUP-101 no los reimplementa ni se los atribuye.

La instrucción original de adaptar #60/#61/#62 **antes de sus merges** describía
la situación del 02/10. Las cuatro PR de origen ya están integradas, según el
[contraste actual](../evidence/JUP-101-continuity.md); no se atribuye un acuerdo
retrospectivo ni se reabren esas ramas. Las ramas futuras pueden aplicar el
procedimiento anterior. La excepción de cierre siguiente sólo se aplica a JUP-101.

## Conformidad y excepción de cierre

[Paris expresó conformidad el 04/10](https://github.com/EconomiconFinOps/tfm-economicon/pull/64#issuecomment-5974860953)
con índice y referencia únicos, temas estables, conservación de aportaciones y
fuentes de verdad. Aclaró que revisión, validación y confirmación de roles siguen
su procedimiento. Se conserva esa conformidad; no prueba pairing ni aprobación
de PR, y no equivale a consenso completo.

Los roles originalmente **propuestos** fueron Alejandro Aguado (liderazgo),
Paris Arcos Martin (pairing), Lucia Mateo (revisión) y Victor Mendez (validación).
Se conservan como historia; no acreditan participación. La ejecución y comprobación
técnica asistidas por Codex se registran bajo la cuenta de Alejandro (`Iber1to`).
El pairing y las reviews independientes no realizados se **dispensan para este
cierre por instrucción del usuario**, sin marcarlos como completados ni atribuirlos
a Paris, Lucia o Victor. La conformidad de Paris permanece limitada a su alcance.

Queda superada para JUP-101 la espera del borrador por acuerdo, roles y reviews:
la adopción del MVP se resuelve excepcionalmente, sin afirmar consenso del equipo.
El cierre exige comprobar la documentación y CI técnico del head final, integrar
por PR #64 usando la facultad administrativa ya existente y enlazar la evidencia
en Trello antes de pasarla a Hecho. No se cambian las reglas de protección ni se
publican reviews del autor como si fueran independientes. El bypass y los requisitos
humanos dispensados quedan visibles; `JUP reviews` no se falsea como satisfecho.

Esta decisión no crea una excepción permanente, no completa otras tarjetas ni
reescribe aportaciones históricas. La prioridad sigue sin etiqueta y no se inventa
una fecha de entrega; la condición de fuera de plazo procede de la instrucción
del usuario. Las correcciones futuras siguen el proceso general de CONTRIBUTING.
