# Informe antes y después del cambio de modelo (plantilla de JUP-133)

Se rellena al terminar la reejecución. La columna «Después» empieza en «No medido» y solo se sustituye por un valor medido con su numerador, denominador y fuente. Plan: [model-reevaluation-plan.md](model-reevaluation-plan.md). Clasificación de las medidas: [inventario](model-dependence-inventory.md).

## 1. Qué se compara

| | Antes | Después |
| --- | --- | --- |
| Alias | `economicon-chat` | `economicon-chat` |
| Modelo servido (`generation_model_id`) | | |
| Proveedor (`generation_provider`) | | |
| Cuantización (`generation_quantization`) | | |
| Configuración del gateway (`gateway_config_sha256`) | | |
| Commit del producto | | |
| Fecha de la ejecución (UTC) | | |
| Identidad atestiguada por el instrumento | No | No |

Los valores de identidad son los que declara la configuración del gateway. El instrumento no verifica qué modelo respondió; si cambiara el contrato de JUP-035 para atestiguarlo, esta fila lo diría.

## 2. Medida a medida

Una fila por medida clasificada `dependiente` en el inventario.

| Medida | Antes (valor, n/d, IC95) | Después (valor, n/d, IC95) | Condiciones iguales | Lectura |
| --- | --- | --- | --- | --- |
| Robustez: aciertos de 29 | | No medido | | sin comparación |
| Robustez: prohibiciones incumplidas de 55 | | No medido | | sin comparación |
| Indicadores de las cuatro familias (19 filas) | | No medido | | sin comparación |
| Coste de IA: facturado frente a estimado | | No medido | | sin comparación |
| Coste por consulta | | No medido | | sin comparación |
| Latencia p95 de la campaña | | No medido | | sin comparación |
| Batería N3/N5: conformidad por requisito | | No medido | | sin comparación |

## 3. Reglas de lectura

La columna «Lectura» solo puede decir una de estas cosas, y se aplican por este orden:

1. **sin comparación:** falta alguna de las dos mediciones. No se escribe «mejora» ni «empeora».
2. **límite de la comparación:** las dos existen pero difieren en la batería, el corpus, los parámetros de recuperación o la revisora. La diferencia no se atribuye al modelo.
3. **diferencia no distinguible:** los intervalos de confianza al 95 % se solapan, o no hay intervalo porque la muestra es de una repetición. No se declara dirección.
4. **mejora** o **empeora:** solo si las condiciones son iguales y los intervalos no se solapan, con ambos intervalos escritos en la fila.

Lo no medido se escribe «No medido». Un 0 % solo aparece si se midió un cero.

## 4. Límites de las cifras

Se rellena con los límites de cada medida: tamaño de la muestra, repeticiones, número de revisoras, carácter provisional del informe, periodo cubierto por el coste y alcance de la latencia (campaña frente a tráfico real).

## 5. Gasto

| Concepto | Valor |
| --- | --- |
| Presupuesto autorizado | 1,5 USD |
| Gasto real del gateway | |
| Gasto real contrastado con OpenRouter | |
| Muestras sin medir por llegar al tope | |

## 6. No se reevaluó

Una fila por cada medida `dependiente` que no se repitió, con el motivo por escrito y la cifra de la memoria que queda «obsoleta sin sustituto». Las medidas `independiente` e `historica` no se listan aquí: su motivo está en el inventario.

| Medida | Motivo | Cifra de la memoria afectada |
| --- | --- | --- |
| | | |

## 7. Dónde se ve

Capturas del dashboard de evaluación en Grafana con las ejecuciones de ambos modelos como ejecuciones distintas y sin serie compartida: `docs/evidence/JUP-133/`.
