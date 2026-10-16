# Política de revisiones de PR — JUP-126

Actualizado:2026-10-16. Origen:«Preparar la corrección de JUP reviews en una PR
separada de gobernanza»,chat01a12c49-7488-72f0-9077-1137c5c4f2a6.
[Trello](https://trello.com/c/SplMvNMA). Base53b43bb1; rama
fix/JUP-126-dismissed-review-titles, copia aislada.

Causa:el cómputo histórico incluye títulos desestimados;PR63 detecta solapamiento
lmatsan aunque su validación5402336106 está DISMISSED. Se propone último título
por persona/tipo;desestimado no aporta rol y no revive anterior. Historial
completo para decisiones de cambios;proceso2026-10-16 sincronizado en AGENTS y
CONTRIBUTING,spec y tests actualizados. No cambiar dictámenes ni excepciones.

[Evidencia propia](../evidence/JUP-126-validation.md):63 política,14workflow,
14gobernanza,73OpenSpec y4mutantes detectados. Fixture18reviews sólo metadatos.
CI del SHA publicado y revisión Paris/validación Víctor pendientes;Lucía pairing
asignado sin acreditar. Roles confirmados por usuario. Esta PR no acredita los
roles automáticamente ni aceptación generativa,ni autoriza merge de PR63.

Próximo:publicar PR separada,comprobar CI y solicitar ambos dictámenes,conservar
la tarjeta sin cerrar. No tocar JUP-100 cerrado ni asignaciones de PR63.

## Reconciliacion con develop — 2026-10-16

Se incorpora develop 22f0e2f3 (JUP-121/PR132) sobre 098c50aa. Unico conflicto:
el indice; conservadas ambas filas. Todos los cambios disjuntos de ambas ramas
contrastados con Git, sin diferencias. Politica, fixture y pruebas propios intactos;
CI entrante conservada, incluido evaluation-dashboard:test y timeout de20min.
Pruebas propias:63 politica,14 gobernanza,14 workflow; OpenSpec74/74,
trazabilidad7 e higiene1692 correctas. Dos avisos de whitespace proceden de
develop; diff propio contra develop limpio. CI del nuevo SHA pendiente de
publicacion. Revision favorable de Paris sobre098c50aa conserva fecha/alcance;
validacion Victor, pairing y revalidacion de dependencias pendientes. No merge
a develop, nuevas excepciones, ejecucion generativa ni cambios en dictamenes.
