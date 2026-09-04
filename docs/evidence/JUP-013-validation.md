# Evidencia de validacion JUP-013

- Fecha: 2026-08-26.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-013-normalize-azure-costs` hacia `develop`.
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/14.
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

- Processor: `133 passed` con Python 3.12.
- Azure Cost API: `58 passed`.
- Backend: `10 passed`.
- Gobierno: JUP, politica de PR, CI, roadmap, repositorio, corpus, gateway e
  higiene superados.
- OpenSpec estricto: `17 passed, 0 failed`.
- Build de frontend de produccion superado.
- `git diff --check` y compilacion Python superados.
- CI remota inicial: seis checks superados en
  https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33005896036.

## Validacion real en dockerserver

Se construyeron imagenes limpias de API y processor desde `bba770f` y se
levantaron CockroachDB 24.1.11 y la API simulada en un proyecto Docker aislado.
El entorno temporal y sus volumenes se retiraron al finalizar.

- Migraciones aplicadas: `001`, `002` y `003`.
- Slice por defecto `ResourceGroup + ServiceName`: 34 filas; las 34 contienen
  ambos campos tipados.
- Slice `Project + CostCenter`: 23 filas; 16 con tags y 11 con proyecto `Foo`.
- Repeticion del slice por defecto: mismo run ID
  `416193ab-2ecc-5247-b609-8e1eec396a85` y 34 filas, sin duplicados.
- Run ID de tags/proyecto: `2b7b7f60-84ce-5a9c-8993-6afeca571aa4`.

La salida solo contiene scopes, IDs, contadores y dimensiones del dataset
publico. No contiene credenciales ni se ha enviado ningun mensaje a Discord.

## Decisiones

Los campos dimensionales son opcionales porque Azure Cost Query solo devuelve
las agrupaciones solicitadas. La suscripcion de alcance permanece obligatoria en
la tabla y procede del path de la consulta. JUP-013 no construye la jerarquia de
JUP-014 ni calcula los KPIs de JUP-026.
