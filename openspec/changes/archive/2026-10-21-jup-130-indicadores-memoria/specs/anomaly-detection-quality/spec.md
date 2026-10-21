## ADDED Requirements

### Requirement: Eventos inyectados independientes del detector
El sistema DEBE (SHALL) medir el detector de episodios contra una lista versionada de eventos inyectados escrita a partir del generador de datos (`anomaly_levels()`), nunca a partir de la salida del detector ni del fichero de esperados de JUP-107. Cada evento lleva servicio, día de inicio, naturaleza y si es detectable por diseño. Una prueba DEBE (SHALL) comprobar que cada evento corresponde a un salto real del generador y que todo salto significativo del generador tiene su evento.

#### Scenario: Evento sin salto en el generador
- **WHEN** la lista contiene un evento cuyo servicio y día no presentan un salto de coste en el generador
- **THEN** la prueba falla indicando el evento

#### Scenario: Salto del generador sin evento
- **WHEN** el generador introduce un salto de coste que ninguna entrada de la lista cubre
- **THEN** la prueba falla indicando el servicio y el día

#### Scenario: Caída de coste
- **WHEN** el generador baja el coste de un servicio (por ejemplo Compute el 4 de octubre)
- **THEN** no se considera un evento a detectar, porque la regla del detector solo vigila aumentos

### Requirement: Precisión, recall y retraso del detector
El sistema DEBE (SHALL) ejecutar la planificación real de episodios (`plan_detection`) sobre los datos del generador con una fecha de referencia dada, empezando desde un estado vacío, y calcular tres medidas: precisión (episodios con evento / episodios abiertos), recall (eventos detectados / eventos) y retraso en días entre el inicio del evento y la apertura del episodio. Un evento cuenta como detectado si un episodio del mismo servicio abre entre el día del evento y tres días después, y cada episodio se empareja con un solo evento.

#### Scenario: Medición a la fecha de referencia del fin de datos
- **WHEN** se mide con la fecha de referencia 2026-10-30
- **THEN** el informe recoge los eventos del 9 de septiembre al 20 de octubre, los episodios abiertos, los verdaderos positivos, los falsos positivos y los falsos negativos
- **AND** cada recuento se puede conciliar con la lista de episodios impresa

#### Scenario: Episodio sin evento
- **WHEN** el detector abre un episodio que ningún evento explica
- **THEN** cuenta como falso positivo y baja la precisión

#### Scenario: Sin episodios abiertos
- **WHEN** el detector no abre ningún episodio
- **THEN** la precisión es `not_measured` con denominador 0, no 1 ni 0

#### Scenario: Un episodio no cubre dos eventos
- **WHEN** dos eventos del mismo servicio caen dentro de la tolerancia de un mismo episodio
- **THEN** el episodio se empareja con uno solo y el otro cuenta como no detectado

### Requirement: Dos recalls que separan la limitación de la regla
El sistema DEBE (SHALL) informar el recall sobre todos los eventos y, por separado, el recall sobre los eventos detectables por diseño, sin mezclarlos. Un evento no es detectable por diseño cuando la semana de referencia de su servicio es cero (la regla exige referencia positiva), por ejemplo un pico desde cero o la primera aparición de un servicio.

#### Scenario: Pico desde cero
- **WHEN** Backup pasa de 0 a 300 EUR en un día
- **THEN** el evento figura como no detectable por diseño y su fallo penaliza el recall de todos los eventos pero no el de los detectables

#### Scenario: Detectable no detectado
- **WHEN** un evento detectable por diseño no abre episodio
- **THEN** penaliza ambos recalls y se lista como hallazgo del detector

### Requirement: Salida de la medición de anomalías
El sistema DEBE (SHALL) emitir un informe `rows-v1` con fuente `JUP-130-anomalies`, grupo `anomaly_detection`, tipo A y juicio automático, que lleva la fecha de referencia y el commit, y una tabla Markdown reproducible con el comando que la genera. El informe y la tabla DEBEN (SHALL) declarar que los datos son sintéticos, que hay pocos eventos y que las etiquetas las escribió quien diseñó los datos.

#### Scenario: Reproducción
- **WHEN** se repite el comando con el mismo commit y la misma fecha de referencia
- **THEN** el informe y la tabla salen idénticos byte a byte

#### Scenario: Declaración de límites
- **WHEN** se lee la tabla de la memoria
- **THEN** incluye que no demuestra validez estadística ni comportamiento con facturas reales
