# JUP-037 — Atribución y excepción de plazo del MVP

Fecha: 10/10/2026, Europe/Paris. [Trello](https://trello.com/c/n4Aplko2),
[PR100](https://github.com/EconomiconFinOps/tfm-economicon/pull/100).

El usuario ordenó en el chat de refinamiento: «Estamos fuera de fecha, completa
todas las tareas necesarias marcando en la atribucion la excepcion por estar
fuera de plazo para la entrega del MVP». ID de ese chat no confirmado.
Esta autorización supera para JUP-037 la espera anterior por pairing/dictámenes;
no modifica el proceso general ni autoriza atribuciones falsas a otros miembros.

| Rol originalmente asignado | Persona | Participación efectivamente acreditada en este cierre |
| --- | --- | --- |
| Liderazgo | Alejandro Aguado (`Iber1to`) | Refinamiento, publicación e integración de PR100; implementación y comprobaciones con asistencia de Codex |
| Pairing/coautoría | Lucia Mateo | No realizada/acreditada; exceptuada para esta entrega por plazo MVP |
| Revisión de PR | Paris Arcos Martin | No hay dictamen suyo; exceptuado por plazo MVP |
| Validación, pruebas y documentación | Victor Mendez | No hay dictamen suyo; exceptuado por plazo MVP |

La revisión técnica y la validación de cierre las realiza el liderazgo con
asistencia de Codex, sin independencia respecto a la autoría. **No** son
`Revision JUP-037` o `Validacion JUP-037` de otras personas ni aprobaciones GitHub
del autor sobre su PR. No se publican reviews inventadas para satisfacer el check.

Se autoriza el cierre del incremento MVP existente: selección estructurada de
project/application/owner/cost_center/tag y evidencia persistida. No se declara
lenguaje natural libre, datos application/owner desplegados, stack completo ni
combinación con JUP-036/PR69. Se conservan sus límites explícitos.

La integración excepcional de la PR existente debe usar el mecanismo administrativo
PR-only disponible, con CI técnica del head final en verde y sin solicitudes de
cambios pendientes. No alterar checks, rulesets, CONTRIBUTING ni ramas protegidas
por push directo. `JUP reviews` puede seguir fallando por la ausencia real de ambos
dictámenes; la excepción se documenta, no se hace pasar ese check artificialmente.

[Evidencia del cierre](../evidence/JUP-037-mvp-exception.md). Trello y la descripción
de PR registran la excepción antes de integrar; el SHA de merge y el readback de
Hecho se registran al ejecutarse. No hay despliegue, gasto ni envío a Discord.
