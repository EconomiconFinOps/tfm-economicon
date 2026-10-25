# Diseño JUP-126: autorización aislada de PR135

Trello: https://trello.com/c/SplMvNMA

## Decisión y guardas
Sólo número135 autoritativo (evento para política, respuesta API para reviews),
repositorio canónico, autorIber1to, rama existente, base develop, tarjeta126,
cuatro declaraciones de rol exactas y un marcador visible único activan el caso.
Los nombres conservan normalización de mayúsculas/acentos, no alias inventados.
El lector específico excluye comentarios, HTML y código cercado/indentado o spans
multilínea; no cambia la excepción general anterior. Marcador visible en contexto
incorrecto falla de forma cerrada. No se añade el marcador a la plantilla general.

## Títulos y decisiones
Sólo lmatsan/Revision y ParisArcos/Validacion aportan títulos en ese caso. Se elige
último título antes de excluir desestimados y antes de restringir identidades;
no resucitan títulos. Los títulos de asignaciones históricas siguen publicados.
`published` completo sigue resolviendo Request changes, incluidas complementarias;
Comment no las levanta. No se infiere aceptación de contenido ni del SHA actual.

## Autorización y límites
Fuente humana literal de18/10/2026 en HAL9000, chat01a1270c-e332-7462-9c90-706d49ade92c:
«Autorizo la excepción puntual para que Lucía mantenga pairing y revisión en la PR135,
con Paris en validación. Déjalo documentado y desbloquea el cierre sin tocar las demás PR».
La instrucción posterior exige soporte mínimo aislado en código, sin bypass global,
mark-success, desestimaciones o cambios de protecciones. No autoriza merge previo
a dictámenes favorables y autorización aplicable.

## Validación
Regresiones positivas/negativas de identidad, roles, declaración oculta, ambos
títulos, autor/borradores, desestimación sin resurrección y cambios complementarios.
Contrafactual contra93c0dd8f y pruebas de los lectores evento/API; CI/SQL del SHA final.
No repetir campañas B/N5, producto o suites no afectadas localmente.
