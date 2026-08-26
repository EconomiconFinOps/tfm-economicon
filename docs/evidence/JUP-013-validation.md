# Evidencia de validacion JUP-013

- Fecha: 2026-08-26.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-013-normalize-azure-costs` hacia `develop`.
- Tarjeta: https://trello.com/c/vw0xIKRN.
- Liderazgo: Alejandro Aguado; pairing: Lucia Mateo; revision: Paris Arcos
  Martin; validacion, pruebas y documentacion: Victor Mendez.

## Alcance implementado

- Contrato FinOps explicito sobre el normalizador de JUP-077.
- Alias EA, FOCUS y Azure Query reconciliados sin duplicar la ingesta.
- Resource group, servicio, proyecto, tags y consumo opcional tipados.
- Dimensiones desconocidas preservadas y tags legacy parseados de forma tolerante.
- Hash estable entre aliases equivalentes y rechazo de contradicciones.
- Migracion 003 aditiva, backfill e indices de analisis.
- Repositorio SQL actualizado para persistir y recuperar los nuevos campos.
- Consulta por defecto de resource group y servicio.

## Validacion

- Processor focal: `133 passed` con Python 3.12.
- Suite completa y recorrido Docker: pendientes de registrar antes del PR.
- CI remota: pendiente.

## Decisiones

Los campos dimensionales son opcionales porque Azure Cost Query solo devuelve
las agrupaciones solicitadas. La suscripcion de alcance permanece obligatoria en
la tabla y procede del path de la consulta. JUP-013 no construye la jerarquia de
JUP-014 ni calcula los KPIs de JUP-026.
