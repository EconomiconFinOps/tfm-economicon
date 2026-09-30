## JUP

- ID: JUP-XXX
- Trello: https://trello.com/c/REEMPLAZAR

## Cambio

Describe el objetivo, el alcance incluido y lo que queda fuera.

## Participacion

- Liderazgo:
- Pairing/coautoria:
- Revision de PR:
- Validacion, pruebas y documentacion:

<!-- Si revision y validacion las hace excepcionalmente la misma persona, acordado en Trello, anade en una linea propia: - Excepcion: revision y validacion por la misma persona, acordado en Trello -->

## Validacion

Evidencia del lider: incluye comandos ejecutados, resultados y enlaces a evidencias versionadas. No sustituye a la review `Validacion JUP-XXX` de quien valida.

## Checklist

- [ ] La rama sigue `tipo/JUP-XXX-descripcion` y no es `main`.
- [ ] El titulo contiene el mismo `JUP-XXX` que la rama.
- [ ] La tarjeta Trello esta enlazada directamente.
- [ ] No se han incluido secretos ni credenciales.
- [ ] Las pruebas aplicables estan en verde.
- [ ] La documentacion y las decisiones se han actualizado.
- [ ] Los cuatro roles tienen una persona identificada.
- [ ] Si un rol se ha reasignado, la seccion Participacion y la tarjeta Trello lo reflejan.
- [ ] Revision y validacion se publicaran como dos reviews separadas, `Revision JUP-XXX` y `Validacion JUP-XXX`, segun el flujo de CONTRIBUTING.md#review-and-validation-flow.
- [ ] Quien revisa y quien valida no suben commits a esta rama; los findings fuera de alcance se piden al lider.
- [ ] Antes de atender cambios o mergear se leen todas las reviews, los comentarios de la conversacion y los comentarios en linea del diff.
- [ ] Si "Update branch" trae cambios que tocan lo mismo que este PR, se pide una revalidacion antes de mergear.
- [ ] El PR apunta a `develop`; solo `develop` puede proponer cambios a `main`.
