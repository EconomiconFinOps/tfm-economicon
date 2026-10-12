# Preguntas probables y qué enseñar

Respaldo para la ronda de preguntas. Cada fila dice qué paso de [guion.md](guion.md) responde y en una línea qué contestar. Se enseña **solo ese paso**, con los datos ya cargados ([preparacion.md](preparacion.md)). Recordad siempre que los datos son **sintéticos**: se dice antes de enseñar la cifra.

| Pregunta | Paso | Respuesta en una línea |
| --- | --- | --- |
| ¿Soporta más de una moneda? | D3, D6 | Sí: EUR y USD se muestran por separado, con su propio total y su propia comparación; nunca se suman entre sí. |
| ¿Qué pasa si falta un mes, un hueco en la serie? ¿Se rellena con ceros? | D4 | No: un mes sin datos se marca como «Sin datos de esta moneda» y el gráfico deja un hueco; solo se muestra un cero si existe un registro de cero. |
| ¿Distingue un coste cero de la ausencia de datos? | D4 | Sí: febrero tiene un cero registrado (0.00, 1 registro) y marzo no tiene datos (—). |
| ¿Cómo trata los créditos o importes negativos? | D5 | Entran en el total y en la comparación con su signo; mayo es un crédito de -50.00 EUR. |
| ¿Cómo se calcula la comparación entre meses? | D5, D6 | Último mes con coste menos primer mes con coste del periodo y moneda; un mes con cero registrado no es extremo. |
| ¿Qué pasa con importes muy grandes? | D11 | Opcional: por encima del rango seguro de un número de JavaScript no se dibuja, se avisa y el valor exacto queda en la tabla. |
| ¿Se pueden repartir los costes por etiqueta? | D7 | Sí: agrupando por Etiqueta con una clave, aquí `cost_center`; lo que no tiene etiqueta queda en «Sin dimensión». |
| ¿Qué pasa con los registros sin fecha o sin dimensión? | D8 | No se reparten ni se esconden: se avisan como datos parciales y se cuentan aparte. |
| ¿Un cliente ve los costes de otro? | D9 | No: al cambiar a Core Finance no aparece ningún coste de Growth Ops. Es una demostración visual; el aislamiento está cubierto por sus propias pruebas. |
| ¿Por qué pone «Azure» en pantalla si los datos no son de Azure? | D1 | Los rótulos de la interfaz dicen Azure porque los datos tienen la forma de los costes de Azure, pero son sintéticos: no son facturas ni proceden del dataset público. |
| ¿Son datos reales? | D1, D10 | No: son datos sintéticos creados para probar la aplicación; no vienen de Azure ni del dataset público. |
| ¿Funciona el ahorro potencial o las recomendaciones con estos datos? | D10 | No: esas pantallas usan datos fijos de la maqueta y no salen de estos costes; el ahorro potencial no está disponible. |
| ¿Cómo detecta y prioriza las anomalías? | D12 | Revisa el coste de cada día de cada servicio con la regla de negocio y ordena por criticidad, calculada sobre el impacto acumulado de cada anomalía (Compute, 2807.71 EUR). |
| ¿Una anomalía dice la causa? | D12 | No: es una candidata para investigar; la causa no está establecida y la cierra una persona con un motivo. |
| ¿Por qué una subida no abre una anomalía? | D12 | Porque la regla exige superar lo esperado a la vez en importe y en porcentaje; un servicio nuevo, sin gasto previo, tampoco la abre. |

No improvisar cifras: si una pregunta no está en la tabla, decir que no se ha comprobado con estos datos.
