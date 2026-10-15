# Preguntas probables y qué enseñar

Respaldo para la ronda de preguntas. Cada fila dice qué paso de [guion.md](guion.md) responde y en una línea qué contestar. Se enseña **solo ese paso**, con los datos ya cargados ([preparacion.md](preparacion.md)). Recordad siempre que los datos son **de demostración** (sintéticos, o públicos con las fechas desplazadas): se dice antes de enseñar la cifra.

| Pregunta | Paso | Respuesta en una línea |
| --- | --- | --- |
| ¿Soporta más de una moneda? | D3, D6 | Sí: EUR y USD se muestran por separado, con su propio total y su propia comparación; nunca se suman entre sí. |
| ¿Qué pasa si falta un mes, un hueco en la serie? ¿Se rellena con ceros? | D4 | No: un mes sin datos se marca como «Sin datos de esta moneda» y el gráfico deja un hueco; solo se muestra un cero si existe un registro de cero. |
| ¿Distingue un coste cero de la ausencia de datos? | D4 | Sí: en dólares, agosto tiene un cero registrado (0.00, 31 registros) y julio no tiene datos (—). |
| ¿Cómo trata los créditos o importes negativos? | D5 | Entran en el total y en el desglose con su signo; agosto incluye un crédito de -250.00 EUR en el grupo Credits. |
| ¿Cómo se calcula la comparación entre meses? | D5, D6 | Último mes con coste menos primer mes con coste del periodo y moneda; un mes con cero registrado no es extremo, y con un solo mes con coste no hay comparación. |
| ¿Qué pasa con importes muy grandes? | D11 | Opcional: por encima del rango seguro de un número de JavaScript no se dibuja, se avisa y el valor exacto queda en la tabla. |
| ¿Se pueden repartir los costes por etiqueta? | D7 | Sí: agrupando por Etiqueta con una clave, aquí `project`; lo que no tiene etiqueta queda en «Sin dimensión». Solo hay servicio y proyecto en estos datos. |
| ¿Qué pasa con los registros sin servicio o sin dimensión? | D8 | No se reparten ni se esconden: se avisan como datos parciales y se cuentan aparte. |
| ¿Un cliente ve los costes de otro? | D9 | No: al cambiar a Core Finance aparecen sus propias cifras, no las de Growth Ops. Es una demostración visual; el aislamiento está cubierto por sus propias pruebas. |
| ¿Por qué pone «Azure» en pantalla si los datos no son de Azure? | D1 | Los rótulos de la interfaz dicen Azure porque los datos tienen la forma de los costes de Azure, pero son de demostración: no son facturas de Azure de 2026. |
| ¿Son datos reales? | D1, D10 | No: son datos de demostración, sintéticos o del dataset público con las fechas desplazadas; no son facturas reales de Azure de 2026. |
| ¿Funciona el ahorro potencial o las recomendaciones con estos datos? | D10 | No: las pantallas de recomendaciones, recortes y coste detallado no se publican y el ahorro potencial no está disponible. |
| ¿Por qué la fecha de la cabecera dice «simulada»? | D1 | Porque la aplicación muestra datos solo hasta una fecha de referencia fijada por configuración (aquí 30/10/2026); sin configurarla sería el día real. |
| ¿Cómo detecta y prioriza las anomalías? | D12 | Revisa el coste de cada día de cada servicio con la regla de negocio y ordena por criticidad, calculada sobre el impacto acumulado de cada anomalía (Compute, 5851.57 EUR). |
| ¿Una anomalía dice la causa? | D12 | No: es una candidata para investigar; la causa no está establecida y la cierra una persona con un motivo. |
| ¿Por qué una subida no abre una anomalía? | D12 | Porque la regla exige superar lo esperado a la vez en importe y en porcentaje; un servicio nuevo, sin gasto previo, tampoco la abre. |

No improvisar cifras: si una pregunta no está en la tabla, decir que no se ha comprobado con estos datos.
