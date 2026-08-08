# ADR-0001: API Azure Cost Management simulada

- Estado: Proposed
- Fecha: 2026-08-08
- Tarjeta Trello: JUP-073 — https://trello.com/c/ll3GzmuN
- Pull request: pendiente
- Sustituye a: ninguno
- Sustituido por: ninguno

## Contexto

Economicon debe demostrar ingesta FinOps Azure, pero el equipo no dispone de un
tenant real. Leer el dataset público directamente no permite probar el conector,
la paginación ni los errores de una API.

## Decisión propuesta

Crear en JUP-074 un servicio independiente `apps/azure-cost-api` que implemente
únicamente el contrato definido en `docs/api/azure-cost-query.openapi.json`.
Servirá fixtures del dataset público y permitirá cambiar posteriormente a
`management.azure.com` mediante configuración del cliente.

## Consecuencias

El recorrido será reproducible y permitirá pruebas integradas sin credenciales
Azure. El equipo deberá mantener pruebas de contrato y dejar claro que el
servicio no es un emulador completo ni evidencia de conexión a Azure real.

## Alternativas consideradas

- Leer CSV directamente: más simple, pero no valida comportamientos HTTP.
- Contratar un tenant: descartado por decisión de alcance y coste.
- Mock interno del processor: acoplaría la ingesta al dataset y ocultaría
  paginación y errores.

## Aprobación

El estado pasará a `Accepted` cuando la PR de JUP-073 reciba la revisión y
validación previstas en Trello.
