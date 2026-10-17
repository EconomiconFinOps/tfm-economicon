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
- deteccion conceptual de anomalias sobre gasto observado;
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
