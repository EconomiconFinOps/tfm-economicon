# Convención compartida de continuidad

Verificación: 2026-10-02. Origen: [JUP-101](https://trello.com/c/ReMOdXEK), a partir
de la [observación de Víctor](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5385253656).
Estado: propuesta pendiente de acuerdo del equipo.

## Convención propuesta

- Mantener un único índice `docs/continuidad/README.md` y una sola referencia desde
  `AGENTS.md`. Leer el índice y únicamente los temas relevantes antes de trabajar.
- Usar un archivo estable por tema, con problema, alcance, decisiones y motivos,
  evidencias y comandos reproducibles, fecha de verificación y siguientes pasos.
- Distinguir hechos, hipótesis y pendientes; marcar lo superado. Enlazar revisiones
  y tarjetas para el estado operativo, sin crear un backlog alternativo.
- Actualizar el tema y el índice tras hitos relevantes. Conservar los cambios de
  otros colaboradores; nunca sustituir el índice por la versión de una sola rama.
- No registrar credenciales ni datos de sesión. Usar rutas relativas del proyecto
  y enlaces permanentes cuando los documentos enlazados vayan a moverse.

## Integración de las ramas abiertas

PR #55 retira su adición de continuidad y de AGENTS.md; sus resúmenes se conservan
junto a esta propuesta. Su corrección funcional puede revisarse por separado.
Las PR #60, #61 y #62 siguen conteniendo sus propios temas y no se modifican aquí.
Cuando se integre la convención, actualizar esas ramas desde develop, resolver
cada add/add del índice conservando la unión de filas y mantener una sola frase
de AGENTS.md. Revisar que cada enlace relativo tenga destino en la rama resultante.
No usar una resolución global ours/theirs que descarte temas ajenos.

No se acredita que esos conflictos futuros estén resueltos: depende del orden de
merge y de la aceptación del equipo. Siguiente paso: acordar esta convención y
aplicarla a cada PR al actualizar su base.
