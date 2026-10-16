# JUP-126 — Corrección de títulos desestimados

Fecha:2026-10-16. [Trello](https://trello.com/c/SplMvNMA).
Base:develop53b43bb1e79b08967cc1b9efdf66669f11e8197c.
Rama:fix/JUP-126-dismissed-review-titles.

## Problema y cambio
PR63 cuenta la Validacion desestimada5402336106 de lmatsan junto con su Revision
complementaria5513541546 y exige una excepción inexistente. La regla anterior,
su test y la spec JUP-100 contaban descartadas: se cambia explícitamente ese
contrato de gobernanza, sin editar ningún dictamen.

Último título por persona/tipo/tarjeta, descartado después de seleccionar el
último. No se recupera un título anterior si el último está DISMISSED. Historial
completo y cálculo de solicitudes de cambios preservados. Los roles asignados,
comentarios complementarios y acuerdos siguen sujetos al proceso humano.

## Comprobaciones propias

| Comando | Resultado |
| --- | --- |
| corepack pnpm pr:check:test |63/63 PASS |
| corepack pnpm ci:check:test |14/14 PASS |
| corepack pnpm repository:governance:test |14/14 PASS |
| corepack pnpm jup:check:test |PASS |
| corepack pnpm jup:check:all |PASS |
| corepack pnpm jup:cleanup:check |PASS |
| corepack pnpm openspec:validate |73/73 PASS |

Cuatro mutantes aislados detectados por fallo de tests:contar DISMISSED,
filtrarlas antes de seleccionar (resurrección),quitarlas del historial completo
(resurrección de Request changes),permitir que COMMENTED levante Request changes.
El código candidato no se modifica durante esas ejecuciones.

Fixture `tools/fixtures/pr-reviews/pr63-20261016.json`:18reviews,primera línea,
login,estado y fecha del corte observado sobre39baec24. El cuerpo de la PR se
vacía deliberadamente:reproduce que NO hay excepción. El original produce el
error de solapamiento;el candidato no. No contiene contenido probatorio de las
reviews y no sirve para validar sus conclusiones. Prueba del original conservada
en el prototipo local del16/10;test de regresión ejecutado en esta rama.

Dependencias instaladas desde lockfile con caché offline,sin cambios de lockfile.
Logs locales:materiales/07-evidencias/JUP-reviews-gobernanza-2026-10-16/ del workspace.
CI remota del SHA publicado pendiente al redactar;el recibo final se enlaza en PR.
No se ejecuta runtime/LLM ni despliegue:el diff afecta sólo política y documentación.

## Revisión y límites
Roles confirmados por el usuario:Alejandro liderazgo,Lucía pairing,Paris revisión,
Víctor validación. No se acredita pairing realizado ni dictámenes de esta PR.
Los resultados anteriores son evidencia propia, no Revision/Validacion oficiales.
El archivo técnico de OpenSpec no implica aceptación de la política.

El check no vincula nombres libres a logins ni interpreta contenido favorable,
SHA vigente o autorización para merge. Sigue sujeto a roles de Trello y punto7
de CONTRIBUTING. No relaja solapamiento vigente sin excepción,errores de API,
autor/borradores ni solicitudes de cambios de revisores complementarios.
PR63 tiene validación de Víctor sobre39baec24;esta corrección no sustituye la
revisión de Paris ni acredita ensayo generativo. No merge ni modificación de
PR63/dictámenes,excepciones,permisos,workflow,rulesets o mensajes Discord.
