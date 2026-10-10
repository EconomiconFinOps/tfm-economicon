# Métricas funcionales de negocio — JUP-068

[Trello](https://trello.com/c/JYaiGKKv) · [Registro de ejemplo](JUP-068-example.json) · [Evidencia técnica](../evidence/JUP-068-validation.md)

Este instrumento define cómo medir valor funcional del MVP. Calcula registros
aportados por el equipo, offline y sin dependencias nuevas. No obtiene datos de
Azure, ejecuta consultas al asistente ni demuestra beneficios reales por sí mismo.
Versión del contrato: `schema_version: 1`. Las reglas de allocation proceden de
[las reglas internas MVP](../assistant-corpus/business-rules/economicon-mvp-rules.md).
Asignación histórica: Víctor liderazgo, Alejandro pairing/coautoría, Lucía revisión,
Paris validación. El 10/10/2026 el usuario autorizó cerrar esta entrega bajo la
excepción MVP, con ejecución de Alejandro asistida por agente principal y subagente
independiente. No se atribuyen intervenciones ni aprobaciones humanas a los demás.
Los objetivos de piloto siguen siendo hipótesis, no resultados ni consenso del equipo.

## Definiciones y objetivos propuestos

| Métrica | Fórmula y unidad | Objetivo de piloto propuesto, pendiente del equipo |
| --- | --- | --- |
| Tiempo ahorrado | Σ(manual_ms − assisted_ms) de parejas correctas; % = diferencia / Σmanual_ms × 100 | ≥20 % en al menos 10 parejas correctas; publicar también errores y bloqueos |
| Cobertura de gasto asignado | allocated / (allocated + shared + unallocated) × 100 | ≥90 %; publicar shared por separado |
| Ahorro potencial detectado | Σsavings_minor de estimaciones sustentadas y consolidadas por recurso; % sobre el mismo coste elegible | Todas las estimaciones con evidencia, método, owner y riesgo; importe económico sin umbral universal |

Son hipótesis de aceptación para el piloto, no acuerdos ni estándares externos.
El informe no emite un aprobado global. El objetivo económico se debe fijar antes
de medir cuando exista una baseline apta; cero oportunidades puede ser un resultado
legítimo. No se fuerza un ahorro positivo ni se confunde potencial con realizado.
No hay evaluación automática de calidad: JUP-070 determina la conformidad de
respuestas y JUP-071 estudia robustez; [JUP-069](README.md) aporta casos y rúbricas.

## Protocolo de medición

1. Congelar alcance de suscripciones/recursos, dataset, periodo inclusivo,
   moneda, coste actual/amortizado, commit completo y configuración del asistente.
   Documentar completitud de ingesta, exclusiones, créditos y limitaciones en la
   evidencia. Separar registros por moneda, periodo y base de coste; sin conversión
   implícita ni extrapolación mensual/anual. Cada registro tiene una procedencia:
   `synthetic` para datos construidos o `measured` para observaciones ejecutadas.
   Una ejecución con datos sintéticos mantiene `synthetic` y describe qué se ejecutó.
2. Elegir tareas representativas sin adaptar después la muestra al resultado.
   Para tiempo, usar la misma pregunta, contexto congelado y criterio de finalización
   en ambas modalidades. Identificar caso, participante seudonimizado y repetición.
   Calcular `context_sha256` sobre el contexto común real (el ejemplo usa marcadores).
   Alternar orden manual/asistido para reducir aprendizaje; registrar orden,
   condiciones, interrupciones y familiaridad en el fichero de evidencia.
3. Cronometrar desde lectura de tarea hasta respuesta correcta lista para utilizar.
   El tiempo asistido incluye redacción, espera, aclaraciones, comprobación y corrección
   humana. El manual incluye consulta de fuentes y comprobación. Guardar respuesta,
   referencia esperada, tiempos y evaluación para ambas modalidades. `pass` exige
   que las dos sean correctas; una respuesta rápida incorrecta es `fail`. Un fallo
   de infraestructura es `blocked`, una pareja no completada es `not_run`.
   Para incluir una fila hace falta baseline manual positiva. Si aún no se dispone
   de ella, dejar `trials` vacío y registrar tareas pendientes en la evidencia.
4. Conservar todos los intentos, sin borrar fallos: el informe publica los cuatro
   estados y las parejas elegibles. El porcentaje agregado es una razón de sumas,
   no una media simple de porcentajes. Los valores negativos se conservan. Es un
   resultado condicionado a tareas correctas: acompañarlo con la tasa de éxito y
   los tamaños de muestra, sin extrapolarlo a todo el trabajo ni al equipo.
5. Clasificar cada línea de coste exactamente una vez: `allocated` exige owner;
   `shared` exige responsable y regla de reparto; `excluded` exige regla documentada;
   `unallocated` expresa falta de contexto. Un shared gobernado sigue siendo shared
   hasta aplicar y evidenciar reparto. `governed_percent` informa allocated+shared,
   separado de `assigned_percent`. No equivale a cumplimiento de tags (JUP-017).
6. Cuantificar oportunidades solo con baseline y evidencia suficiente para el método
   concreto. Rightsizing necesita utilización/capacidad; facturación sola no basta.
   Registrar owner, riesgo, método reproducible y referencias. Consolidar alternativas
   o efectos interactivos por recurso antes de sumar: el instrumento rechaza dos
   estimaciones del mismo recurso. `candidate` y `not_evaluable` conservan razón,
   evidencia y `savings_minor: null`. Incluir ahorros cero explícitos cuando estén
   evaluados. No estimar ahorro de recursos fuera de la baseline elegible.
7. Una persona comprueba las fuentes originales y registra su evaluación. El
   validador comprueba estructura y coherencia aritmética, no autenticidad de enlaces
   ni corrección semántica de respuestas o recomendaciones. Conservar registro,
   informe JSON, commit y evidencias juntos; no guardar credenciales ni datos personales.

## Contrato del registro

El [JSON de ejemplo](JUP-068-example.json) enumera los campos aceptados. Son
obligatorios `schema_version`, `jup`, `run_id`, `provenance`, `commit`, `scope`,
`dataset_version`, `configuration`, `reviewer`, `period`, `currency`,
`minor_unit_digits`, `cost_basis`, `evidence` y las tres listas. Cada fila tiene
ID único en su lista y evidencia no vacía. Los campos desconocidos se rechazan,
incluida moneda/periodo por fila: normalizar y verificar homogeneidad antes de importar.
Se usan milisegundos enteros positivos y dinero entero en unidades menores
(`minor_unit_digits: 2` significa céntimos). El total no puede superar el rango
entero seguro de JavaScript; los porcentajes se calculan en punto flotante y se
redondean solo al presentar, sin modificar el JSON fuente.

Importes negativos/créditos se rechazan: reconciliar previamente una baseline
no negativa por recurso y documentar el tratamiento; no eliminar créditos para
inflar gasto o ahorro. Líneas cero son válidas. Listas vacías significan falta de
observaciones, no validación del beneficio. Los denominadores cero producen `null`.
Sin estimaciones sustentadas, potencial es `null`; una estimación de cero produce
0. `realized_minor` es siempre `null`: la comprobación posterior de ahorro realizado
queda fuera del alcance. El hash del informe usa SHA-256 del JSON parseado y
serializado por Node; no es el hash de los bytes del fichero ni una firma de evidencia.

```sh
node tools/business-metrics.mjs validate docs/validation/JUP-068-example.json
node tools/business-metrics.mjs report docs/validation/JUP-068-example.json
node --test tools/business-metrics.test.mjs
# Para guardar JSON puro, usar Node directamente:
node tools/business-metrics.mjs report registro.json > informe.json
```

También existen `pnpm business-metrics:validate`, `pnpm business-metrics:test` y
`pnpm business-metrics:report registro.json`. La CLI devuelve 2 por uso
incorrecto y 1 por registro inválido. No necesita red, API keys ni un LLM.

## Ejemplo sintético

Fixture aritmético escrito a mano: 700 EUR allocated, 200 shared, 100 unallocated,
50 excluded. Coste elegible 1.000 EUR; cobertura asignada 70 %, gobernada 90 %.
Dos parejas correctas suman 15 minutos manuales y 9 asistidos: 6 minutos / 40 %
ahorrados. Una pareja tarda un minuto más con asistencia; una respuesta incorrecta
de 10 segundos queda fuera del ahorro y dentro del recuento de fallos.
Una estimación hipotética aporta 140 EUR / 14 % potencial; un candidato sin
utilización no aporta importe. Son resultados de prueba del cálculo, sin medición
del producto ni recomendación ejecutable. No son evidencia de objetivos cumplidos.

## Entrega y límites

Se entrega el método, registro, cálculo y pruebas bajo la excepción MVP autorizada
el 10/10/2026 (chat `01a12707-b0dd-7043-915a-3922cd941a8f`). La revisión asistida
independiente y validación técnica sustituyen las intervenciones humanas pendientes
para este cierre; véase la evidencia enlazada. No se simulan pairing ni reviews humanas.

La captura del piloto sigue sin realizarse: hacen falta tiempos observados de ambas
modalidades, baseline homogénea y oportunidades sustentadas, con calidad conforme
a JUP-069/JUP-070. Es condición para afirmar beneficio real, no un resultado de esta
entrega de definición/instrumentación. Cerrar JUP-068 para el MVP no acredita ahorros,
cumplimiento de los objetivos propuestos ni aprobación de estos por el equipo.
