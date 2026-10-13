## MODIFIED Requirements

### Requirement: Anomalias siempre candidatas y evidenciadas

`detect_cost_anomaly_candidates` SHALL aplicar umbrales versionados a series
deterministas y SHALL devolver candidatos, no causas raiz confirmadas. La serie
es el coste diario observado por servicio y moneda del tenant activo; lo
esperado de un dia es la media diaria de los siete dias anteriores o, con un
episodio abierto, su referencia anclada. Los candidatos persistidos son los
episodios de `cost-anomaly-episodes`: la herramienta SHALL leerlos del tenant
autorizado en lugar de recalcularlos o de usar la consulta de prueba de
`cost-anomaly-detection`. La severidad SHALL derivarse del impacto acumulado
del episodio en su moneda (P1 mayor que 2000, P2 de 500 a 2000, P3 menor que
500), sin conversion de moneda y sin el criterio de impacto critico.

La explicacion de un episodio guardado SHALL ser la de
`anomaly-episode-explanation`: el mismo contenido y la misma evidencia tanto si
se pide por seleccion estructurada en una conversacion como si la solicita la
herramienta. Mientras la herramienta no este registrada y habilitada, el
sistema SHALL ofrecer esa explicacion solo por seleccion estructurada y SHALL
NOT anunciar la herramienta al modelo.

#### Scenario: Doble umbral superado

- **WHEN** la diferencia relativa supera 20 por ciento y la absoluta supera 100 EUR por dia
- **THEN** se genera un candidato con scope, baseline, observado, severidad, evidencia y limitaciones

#### Scenario: Variacion esperada desconocida

- **WHEN** no hay datos de despliegues, trafico o utilizacion
- **THEN** el agente no atribuye una causa y propone investigacion

#### Scenario: Igualdad en los limites

- **WHEN** la diferencia absoluta es exactamente 100 por dia o la relativa es exactamente 20 por ciento
- **THEN** no se genera candidato

#### Scenario: Candidato persistido con reglas versionadas

- **WHEN** el agente explica un episodio guardado
- **THEN** usa su referencia, observado, impacto acumulado, severidad, estado, version de reglas y limitaciones, y lo presenta como candidato sin causa establecida

#### Scenario: Explicacion sin herramienta registrada

- **WHEN** un usuario pide la explicacion de un episodio y el registro de herramientas no contiene `detect_cost_anomaly_candidates` habilitada
- **THEN** recibe la explicacion determinista de `anomaly-episode-explanation` por seleccion estructurada
- **AND** ninguna herramienta de anomalias se anuncia al modelo

#### Scenario: Misma explicacion por las dos vias

- **WHEN** la herramienta se registre y explique un episodio que no ha cambiado desde una explicacion pedida por seleccion estructurada
- **THEN** devuelve las mismas cifras y el mismo identificador de evidencia
