# Arquitectura Funcional Del Producto Economicon

## Proposito

Este documento define contexto funcional sobre Economicon para un asistente orientado a usuarios del producto. No expone arquitectura interna de implementacion, servicios, bases de datos, colas, endpoints, proveedores cloud ni decisiones de despliegue.

La documentacion tecnica completa de componentes, flujos y dependencias queda fuera de este documento. Aqui solo se mantiene una version curada y segura para explicar que hace el producto y que limites tiene en el MVP.

## Vision Del Producto

Economicon es una aplicacion FinOps para analizar costes cloud de Azure en un MVP simulado. Su objetivo es ayudar a entender gasto, asignacion, presupuestos, anomalias y oportunidades de optimizacion usando datos preparados para el producto.

El MVP no conecta con Azure real ni representa un tenant real de cliente. Trabaja con un dataset publico/simulado y con reglas internas documentadas en el corpus.

## Capacidades Funcionales

El asistente puede apoyarse en este contexto para explicar las areas principales del producto:

- visibilidad de costes por periodo, servicio, suscripcion, grupo de recursos, entorno o etiqueta;
- asignacion de costes mediante tags y estados de allocation;
- seguimiento de presupuestos, forecasts y desviaciones;
- deteccion de anomalias de coste como episodios candidatos, con criticidad y seguimiento de estado;
- recomendaciones FinOps de optimizacion, rightsizing, compromisos y mejora de etiquetado;
- explicacion de terminos FinOps y conceptos propios de Economicon.

Estas capacidades describen el comportamiento esperado del producto, no garantizan que cada flujo runtime ya este implementado.

## Modelo Funcional De Datos

El producto organiza la informacion alrededor de cuatro ideas:

- coste observado: importes asociados a recursos, servicios, fechas y dimensiones de analisis;
- contexto de asignacion: tags, owner, cost center, entorno y reglas para separar coste asignado, compartido, no asignado o excluido;
- control financiero: presupuestos, forecast, variacion y senales de desviacion;
- accion recomendada: oportunidades priorizadas con impacto estimado, esfuerzo, riesgo y estado de seguimiento.

El asistente debe usar estos conceptos para responder de forma consistente con las reglas del MVP.

## Guia Del Panel De Anomalias

El panel Anomalias de Economicon muestra las anomalias de coste del cliente activo, ordenadas por criticidad e impacto. Cada anomalia es un episodio candidato: indica que hay que investigar, no que se haya demostrado una causa.

### Detectar anomalias

El panel no detecta nada al abrirse: solo muestra lo ya guardado. Antes de la primera deteccion indica que todavia no se han buscado anomalias en ese cliente.

El boton "Detectar ahora" revisa los costes diarios del cliente con la regla de negocio y guarda los episodios. Repetirlo es seguro. Hacen falta al menos 9 dias con datos del cliente (7 de referencia, el dia que se evalua y el ultimo, que se considera incompleto); si no los hay, el resultado dice que aun no hay datos suficientes. Si no hay dias completos nuevos, dice que ya estaba al dia.

El texto "Revisado hasta" indica el ultimo dia completo evaluado. El ultimo dia con datos no se evalua porque puede estar incompleto. Cuando los datos son sinteticos, el panel avisa de que son datos de demostracion y no facturas reales.

### Leer el panel

El resumen de arriba no cambia con los filtros y solo cuenta las anomalias abiertas (Nueva o Investigando): el impacto acumulado por moneda (las monedas no se suman), cuantas hay abiertas y, de ellas, cuantas son Alta (P1) y cuantas "Ya no se observan". Las cerradas no entran en estas cifras.

La criticidad se muestra como Alta (P1), Media (P2) o Baja (P3), segun el impacto acumulado. La observacion indica si "Se sigue observando" o "Ya no se observa" desde una fecha. Una anomalia que ya no se observa sigue abierta hasta que una persona la cierre.

El estado de una anomalia es Nueva, Investigando, Resuelta o Falso positivo. Se puede filtrar por criticidad, estado y observacion. El boton de exportar descarga las filas filtradas.

### Revisar una anomalia

Al abrir el detalle se ven el impacto acumulado, los dias con impacto, el valor de referencia y las reglas aplicadas, junto con la indicacion "Candidata: causa no establecida" y sus limitaciones.

Desde el detalle una persona puede marcarla como "Investigando" o cerrarla como "Resuelta" o "Falso positivo". Cerrar pide un motivo, no se puede deshacer, y si el gasto vuelve a subir se abre una anomalia nueva. El panel no apaga ni modifica ningun recurso de Azure: solo informa.

Este documento explica como funcionan las anomalias en general. Las cifras de una anomalia concreta (dia de apertura, valor de referencia, impacto acumulado y estado) estan en su detalle y no se pueden deducir de este documento: si el usuario pregunta por una anomalia concreta, hay que indicarle que abra su detalle en el panel y no inventar importes.

## Scope, Dataset Y Tenant

El MVP trabaja con un dataset simulado y no con datos reales de un tenant de cliente. Por eso las respuestas deben diferenciar entre:

- conocimiento global, valido para cualquier usuario del producto;
- conocimiento ligado al dataset simulado del MVP;
- conocimiento tenant-specific futuro, que no esta disponible en el corpus MVP.

Cuando una respuesta dependa de datos reales de cliente, el asistente debe indicar que esa informacion no forma parte del corpus MVP.

## Lo Que El Asistente No Debe Exponer

El asistente no debe usar este documento para responder con detalles internos de implementacion, por ejemplo:

- nombres de servicios internos del repositorio;
- bases de datos, colas, tablas o indices;
- endpoints, cabeceras, workers o healthchecks;
- arquitectura de despliegue;
- proveedores de modelos o decisiones pendientes de ADR;
- credenciales, configuracion operativa o informacion no orientada a usuario final.

Si el usuario pregunta por arquitectura tecnica interna, la respuesta debe remitirse a la documentacion tecnica del proyecto y no inventar detalles.

## Rol Del Corpus Documental

El corpus define conocimiento curado para el asistente. El manifest del corpus indica que documentos son indexables y con que metadata.

El corpus aporta contexto sobre:

- FinOps aplicado al MVP;
- reglas de negocio de Economicon;
- glosario comun;
- contexto funcional del producto.

No debe sustituir la documentacion tecnica completa ni la logica de producto.
