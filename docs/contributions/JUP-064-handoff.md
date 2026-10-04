# Entrega de la implementación de JUP-064 a Víctor

[Trello](https://trello.com/c/wluz6AGW) · rama `docs/JUP-064-team-contributions`
· destino `develop`. Preparación de Alejandro como coautor; Víctor conserva
liderazgo. No existe PR de esta rama en la entrega inicial.

1. Revisar [guía y matriz](README.md), los pendientes por historia y el cambio
   OpenSpec `jup-064-team-contributions`; contrastar alcance y pairing real.
2. Ejecutar el comando de recogida o reproducir el snapshot sin conexión;
   ejecutar `contributions:test`, los checks de gobernanza y OpenSpec.
3. Registrar la contribución propia y el pairing que efectivamente haya ocurrido.
   La implementación de Alejandro no acredita actividad de Víctor automáticamente.
4. Abrir la PR desde la cuenta de Víctor a `develop` con la plantilla existente.
   Enlazar la [evidencia técnica](../evidence/JUP-064-validation.md), conservar
   roles de Trello y pedir review de Lucía y validación de Paris.
5. Resolver feedback, archivar OpenSpec en la rama antes de integrar y regenerar
   el registro si se quiere que incluya también la nueva PR de JUP-064.

Texto preparado para la PR (adaptar solo a las acciones realizadas):

```markdown
## JUP

- ID: JUP-064
- Trello: https://trello.com/c/wluz6AGW

## Cambio

Añade un inventario reproducible de contribuciones por historia y miembro con
roles actuales de Trello, acciones de GitHub y pendientes explícitos. La recogida
usa exclusivamente la integración Economicon para Trello. No acredita pairing
o validación personal a partir de asignaciones, archivos de pruebas o CI.

## Participacion

- Liderazgo: Victor Mendez
- Pairing/coautoria: Alejandro Aguado
- Revision de PR: Lucia Mateo
- Validacion, pruebas y documentacion: Paris Arcos Martin

## Validacion

Ver docs/evidence/JUP-064-validation.md. Pruebas del registro 9/9, gobernanza
80/80, OpenSpec 45/45 y build correctos. Detallar el contraste propio y los
límites de la suite general que constan en esa evidencia.

## Checklist

- [ ] Alcance y pairing real contrastados por el líder.
- [ ] Evidencia técnica y criterios de Trello contrastados.
- [ ] OpenSpec archivado antes de integrar.
- [ ] Review Revision JUP-064 de Lucía y Validacion JUP-064 de Paris publicadas.
- [ ] Leer todo el feedback antes del merge y enlazar reviews desde Trello.
```

Usar también el checklist completo de `.github/pull_request_template.md`; el
texto anterior no declara cumplidas actividades pendientes del equipo.
