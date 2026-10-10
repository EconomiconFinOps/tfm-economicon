# Convención compartida de continuidad

Verificación documental: **2026-10-10**. Origen: [JUP-101](https://trello.com/c/ReMOdXEK)
y [PR #64](https://github.com/EconomiconFinOps/tfm-economicon/pull/64), a partir de
la [observación de Víctor en JUP-025](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5385253656).
Estado: **propuesta implementada documentalmente, pendiente de acuerdo del equipo**.
La autorización del encargo actual permite completar esta entrega; no acredita
consenso, pairing, aprobación ni cierre de la tarjeta.

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

Se resuelve el único conflicto documental del índice conservando sus tres temas:
presupuestos JUP-029, citas JUP-025 y convención JUP-101. El resumen y la fila
histórica de presupuestos se conservan; citas mantiene todo su texto y evidencia
de 01–02/10, con una nota separada de vigencia. AGENTS conserva la regla de memoria
externa y el proceso de reviews JUP-100 de la base actual.

La instrucción original de adaptar #60/#61/#62 **antes de sus merges** describía
la situación del 02/10. Las cuatro PR de origen ya están integradas, según el
[contraste actual](../evidence/JUP-101-continuity.md); no se atribuye un acuerdo
retrospectivo ni se reabren esas ramas. Las ramas futuras pueden aplicar el
procedimiento anterior después de acordar la convención.

## Acuerdo y pendientes humanos

[Paris expresó conformidad el 04/10](https://github.com/EconomiconFinOps/tfm-economicon/pull/64#issuecomment-5974860953)
con índice y referencia únicos, temas estables, conservación de aportaciones y
fuentes de verdad. Aclaró que revisión, validación y confirmación de roles siguen
su procedimiento. Se conserva esa conformidad; no prueba pairing ni aprobación
de PR, y no equivale a consenso completo.

La tarjeta conserva roles **propuestos**: Alejandro Aguado (liderazgo), Paris
Arcos Martin (pairing), Lucia Mateo (revisión) y Victor Mendez (validación).
La comprobación documental del implementador no se atribuye a esas personas
como participación, review o aceptación realizada. No hay quorum definido en
la tarjeta; no se añade uno.

Pendiente del equipo: registrar el acuerdo concreto o las correcciones a esta
propuesta en JUP-101/PR #64, confirmar roles y acreditar el pairing realizado.
Después, solicitar `Revision JUP-101` y `Validacion JUP-101` sobre el head publicado.
El borrador y la tarjeta permanecen abiertos hasta resolver esos pendientes
y cumplir el flujo de integración. La prioridad sigue sin etiqueta; no se infiere
ni se cambia una fecha de entrega.
