# Diseño — JUP-068

CLI offline `tools/business-metrics.mjs` y registro único por alcance, periodo,
moneda y base de coste. La selección de métricas procede de la tarjeta; las reglas
de allocation reutilizan el corpus MVP. Cada intento, coste y oportunidad lleva
evidencia; metadatos y SHA-256 permiten reproducir el informe. El fixture es sintético.

Tiempo: razón de sumas sobre parejas correctas, contando fallos/bloqueos por separado
y preservando ahorro negativo. Cobertura: coste allocated/eligible; shared gobernado
se publica aparte, excluded no entra al denominador. Potencial: oportunidades
sustentadas por recurso, mismo periodo, sin solapamientos; candidatos no cuantifican.
Dinero entero en unidades menores, totales seguros, denominadores cero nulos.

El instrumento valida estructura/coherencia, no demuestra verdad de las evidencias.
Los objetivos se proponen en el protocolo y requieren decisión del equipo antes del
piloto. No hay aprobado automático ni beneficio real acreditado. Captura automática,
API/dashboard y verificación de ahorro realizado quedan fuera de esta definición.

Fuente y protocolo: `docs/validation/JUP-068-business-metrics.md`.
