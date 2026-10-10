# Impacto potencial de recomendaciones — JUP-034

Verificación: 2026-10-10. Encargo «Implementa JUP-034 — Medir impacto potencial de
cada recomendación», delegado desde chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`;
ID del chat de implementación no facilitado.

## Alcance y fuentes

[Trello](https://trello.com/c/Hdwz4SXw), P1 Valor FinOps: ahorro mensual/anual por
recomendación. Registro completo leído de `materiales/07-evidencias/hito-mvp-2026-10-09/backlog-dispatch-source.json`
en el workspace padre; contraste vivo por `DockerServer:/home/danteadmin/economicon-collaboration`
con `TrelloClient.get_cards()` confirma descripción/roles sin cambios.
Lucía lidera, Paris pairing, Víctor revisión, Alejandro validación. No se acredita
participación por asignación ni se reescriben roles.

Copia propia `tfm-economicon-jup034`, rama `feat/JUP-034-impact`, base develop
`c2995a118d419dfe725247bac9c6f219a3f0ea77`. El checkout compartido y ramas ajenas
no se modificaron. Consulta remota sin PR específica previa JUP-034 encontrada.

## Decisiones y entrega

- [Contrato y ejemplo](../contracts/recommendation-impact.md): endpoint autenticado
  sin persistencia; escenarios explícitos del solicitante, no datos verificados.
- Mensual = diferencia positiva; anual ×12 con hipótesis visible de uso/precios
  constantes. Decimal exacto y presentación a dos decimales.
- Monedas separadas; selección descendente determinista de claves de coste
  disjuntas, con `excluded_by`. Factible bajo las claves declaradas, no óptima.
- Desconocido y observado permanecen null; no se interpreta `estimated_savings`
  del procesador, cuyo periodo es desconocido. Dashboard demo intacto.
- JUP-033 simultáneo aporta IDs/evidencias/proyecto/coste observado, sin objetivo
  ni alcance atómico. Contrato concretado; integración con productor pendiente.
- [OpenSpec](../../openspec/changes/jup-034-recommendation-impact/proposal.md)
  conserva gates humanos sin dar por aceptada la implementación.

## Comprobaciones y siguientes pasos

Ver [evidencia por criterio](../evidence/JUP-034-validation.md) para resultados,
versiones y limitaciones. 54/54 pruebas propias, 82 de gobernanza, OpenSpec56/56,
ejemplo55/660 y sintaxis correctos. Batería amplia:355pass/8skip/fallo Windows
en test de salud, reproducido también sobre la base limpia sin JUP-034.
Completar CI y entrega draft, después revisión del
contrato por liderazgo, pairing Paris y dictámenes independientes Víctor/Alejandro.
No fusionar ni cerrar Trello hasta completar el proceso de CONTRIBUTING.
No hay despliegue, ahorro observado, prueba cloud, conexión al frontend ni
validación conjunta del productor JUP-033. No se enviaron mensajes Discord.
La cuenta publicadora configurada es Alejandro; su contribución técnica no
constituye validación independiente. Liderazgo debe regularizar entrega/autoría
y acordar cualquier cambio explícito de roles antes de los dictámenes humanos.
