# ADR-0001: API Azure Cost Management simulada

- Estado: Accepted
- Fecha: 2026-08-25
- Tarjeta Trello: JUP-073 — https://trello.com/c/ll3GzmuN
- OpenSpec relacionado: `jup-073-azure-cost-query-contract`
- Pull request: vinculado a la tarjeta Trello JUP-073 y al historial de GitHub
- Sustituye a: ninguno
- Sustituido por: ninguno

## Contexto

Economicon debe demostrar ingesta FinOps Azure, pero el equipo no dispone de un
tenant real. Leer el dataset público directamente no permite probar el conector,
la paginación ni los errores de una API.

## Decisión

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

## Aprobación y seguimiento

La decisión queda aceptada como base compartida del contrato JUP-073. La
implementación del servicio corresponde a JUP-074, la resiliencia y los modos
de fallo a JUP-075 y el cliente de ingesta a JUP-076. La trazabilidad, revisión
y evidencia técnica se conservan en la tarjeta Trello y en el pull request.
