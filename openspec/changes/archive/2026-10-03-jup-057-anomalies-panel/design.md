# JUP-057 — Priorización de anomalías de prueba

## Contexto

Ruta existente `/anomalies`, protegida por el mismo ciclo de sesión que el resto
de la aplicación. Base inicial de0d62e; reconciliación del 02/10 con develop
5a54ce2, que incorpora JUP-099. El panel usa sus tokens semánticos.

## Decisiones

- Fixtures tipados y locales; no se presenta un contrato definitivo de JUP-030.
- Abiertas = Pendiente o Investigando. Resuelto queda fuera de la vista inicial.
- Criticidad Alta, Media, Baja, con orden descendente y desempate por impacto.
  El selector opcional se retira tras la validación de Victor: los ejemplos
  producían el mismo orden y el contrato solo requiere esta prioridad fija.
- Indicadores calculados sobre el conjunto de ejemplos y claramente etiquetados;
  filtros afectan listado y exportación. No inventar tiempos medios ni tasas.
- Impacto expresado en EUR como estimación del periodo de muestra, sin equipararlo
  a ahorro logrado ni pérdida confirmada. Periodo fijo 18–19 de abril de 2026.
- Filtros accesibles de estado y criticidad, estado vacío con restablecimiento.
- Exportación de las mismas filas ordenadas y filtradas, con identificación demo.
- Colores acompañados por texto, controles apilables y tabla desplazable dentro
  de su región en móvil. No modificar el shell global.

## Límites

No se conectan API, detección en tiempo real, alertas salientes ni mutaciones de
estado. El gráfico, si se conserva, representa una serie simulada independiente
del filtro de anomalías. Los datos ficticios no corresponden al tenant activo.
La integración futura deberá concretar periodo, moneda, criticidad y estados
con JUP-030; no cerrar hallazgos de falta de backend.

## Validación

Pruebas de filas abiertas, métricas, filtros combinados, orden, vacío y exportación.
Fixture adversarial en una suite separada: orden de entrada e impacto distintos
de criticidad, dos altas abiertas y una alta resuelta. Verifica desempate y los
cuatro indicadores globales después de filtrar, también en estado vacío.
Typecheck, lint y build del frontend; suite frontend serial para reducir la
contención ya observada en el proyecto. OpenSpec estricto y trazabilidad/higiene.
Inspección visual desktop/móvil con sesión/API simuladas, identificada como tal.
