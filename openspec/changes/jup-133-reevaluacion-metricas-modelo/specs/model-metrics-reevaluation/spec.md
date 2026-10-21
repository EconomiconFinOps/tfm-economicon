## ADDED Requirements

### Requirement: Inventario de medidas por dependencia del modelo
El sistema DEBE (SHALL) mantener un inventario versionado en `docs/validation/` que clasifique cada métrica, campaña e indicador de evaluación del asistente en exactamente una de tres clases: `dependiente` (su valor cambia si cambia el modelo de generación y hay que repetirla), `independiente` (no depende del modelo y se mantiene) e `historica` (comparativa o medida fechada que se conserva como antecedente y no se repite). Cada entrada DEBE (SHALL) llevar su fuente (tarjeta JUP, informe y ruta), la justificación de la clase y la comprobación en el código o en el informe que la respalda. El punto de partida son las medidas de JUP-035/123 (batería del chat), JUP-070/071 (robustez), JUP-022/067 (métricas técnicas y calibración), JUP-078 (proveedor y coste), JUP-130 (anomalías, coste de IA, frescura de los datos), JUP-068 (tiempo y ahorro) y JUP-063 (comparativa GLM/DeepSeek).

#### Scenario: Cada medida tiene una sola clase
- **WHEN** se valida el inventario
- **THEN** cada entrada tiene una clase de las tres y una justificación no vacía
- **AND** ninguna medida figura en dos clases

#### Scenario: Independiente justificada con el código
- **WHEN** una medida se clasifica como `independiente`, como el detector de anomalías o la frescura de los datos
- **THEN** la entrada nombra la comprobación que muestra que ninguna de sus entradas pasa por el modelo de generación
- **AND** si esa comprobación no se hizo, la medida no puede quedar como `independiente`

#### Scenario: Medida del manifiesto sin clasificar
- **WHEN** el manifiesto `docs/validation/evaluation-runs.json` lista un informe cuya fuente no aparece en el inventario
- **THEN** la validación del inventario falla y nombra la fuente

#### Scenario: Comparativa histórica
- **WHEN** una medida es la comparativa GLM/DeepSeek de JUP-063
- **THEN** se clasifica como `historica`, no se repite y sigue disponible con su modelo

### Requirement: Plan de reejecución con presupuesto autorizado
El sistema DEBE (SHALL) incluir un plan de reejecución que liste, para cada medida `dependiente`, su campaña, el número de llamadas al modelo, el coste estimado en USD, el proveedor y la autorización necesaria. Ninguna reejecución que llame a OpenRouter DEBE (SHALL) empezar sin un presupuesto máximo escrito y la autorización expresa de una persona, y la ejecución DEBE (SHALL) parar al alcanzar ese presupuesto. Una campaña que no se reejecuta DEBE (SHALL) constar con el motivo por escrito.

#### Scenario: Campaña sin autorización
- **WHEN** una campaña dependiente del modelo no tiene presupuesto máximo y autorización registrados
- **THEN** el plan la marca «sin autorizar»
- **AND** su reejecución con gasto no se lanza

#### Scenario: Presupuesto agotado
- **WHEN** el gasto acumulado de una reejecución alcanza el presupuesto autorizado
- **THEN** la ejecución se detiene y el informe indica cuántas muestras quedaron sin medir
- **AND** esas muestras figuran como «no medido» y nunca como fallo ni acierto

#### Scenario: Campaña no reejecutada
- **WHEN** una medida `dependiente` no se reejecuta
- **THEN** el plan y el informe dicen por qué y la cifra afectada de la memoria queda marcada como «obsoleta, sin sustituto»

### Requirement: Informe antes y después sin conclusiones no soportadas
El sistema DEBE (SHALL) producir un informe que compare, medida a medida, la ejecución con GLM-5.2 con la ejecución con DeepSeek V4.1 Flash, mostrando para cada una el valor, el numerador y el denominador, el intervalo de confianza cuando existe y la identidad del modelo. El informe NO DEBE (SHALL NOT) declarar mejora ni empeoramiento cuando falte alguna de las dos mediciones, cuando las dos no sean de la misma batería, corpus y configuración de recuperación, o cuando los intervalos de confianza se solapen. Lo no medido DEBE (SHALL) rotularse «No medido» y nunca mostrarse como 0 %.

#### Scenario: Una de las dos mediciones falta
- **WHEN** una medida tiene valor con GLM-5.2 y ninguno con DeepSeek V4.1 Flash
- **THEN** el informe muestra «No medido» en la columna del modelo nuevo
- **AND** la columna de lectura dice «sin comparación» y no «empeora»

#### Scenario: Intervalos solapados
- **WHEN** los intervalos de confianza al 95 % de las dos ejecuciones se solapan
- **THEN** el informe indica «diferencia no distinguible» y no declara mejora ni empeoramiento

#### Scenario: Condiciones distintas
- **WHEN** las dos ejecuciones difieren en la batería, el corpus o los parámetros de recuperación
- **THEN** el informe lo señala como límite de la comparación y no atribuye la diferencia al modelo

#### Scenario: Gasto frente a presupuesto
- **WHEN** se cierra el informe
- **THEN** incluye el gasto real y el presupuesto autorizado, y lo que no se reevaluó con su motivo

### Requirement: Las mediciones nuevas llegan a Grafana
Toda ejecución nueva de una medida `dependiente` DEBE (SHALL) entrar en el manifiesto versionado `docs/validation/evaluation-runs.json` como `rows-v1` o con el formato de su informe, cargarse con `corepack pnpm evaluation-dashboard:load` y ser visible en el dashboard `economicon-assistant-evaluation` de una pila real de Grafana, no solo en el JSON normalizado. La verificación DEBE (SHALL) comprobar en la pila real que las ejecuciones con GLM-5.2 y con DeepSeek V4.1 Flash aparecen como ejecuciones distintas con su modelo, proveedor y cuantización, que no comparten serie de evolución y que cada panel afectado responde sin error. Las campañas reejecutadas cubren las cuatro familias de indicadores de robustez de JUP-071 (19 filas) y los paneles de JUP-130 que dependan del modelo (coste de IA).

#### Scenario: Ejecución nueva visible
- **WHEN** se carga la campaña ligera de JUP-071 con DeepSeek V4.1 Flash
- **THEN** el panel de ejecuciones y la tabla «Resultados por métrica y ejecución» muestran una columna nueva con su modelo
- **AND** los paneles de indicadores de robustez muestran sus filas

#### Scenario: Series separadas en Grafana
- **WHEN** el dashboard muestra la evolución de una métrica que existe con GLM-5.2 y con DeepSeek V4.1 Flash
- **THEN** no dibuja una línea que una ambas ejecuciones
- **AND** cada una muestra «Sin datos: no hay con qué comparar» mientras no tenga otra ejecución comparable

#### Scenario: Solo se verificó el JSON
- **WHEN** la verificación se hizo con `evaluation-dashboard:rows` y no sobre Grafana real
- **THEN** la evidencia y el informe lo dicen y la tarjeta no puede darse por validada en ese punto

### Requirement: Cifras de la memoria afectadas
El sistema DEBE (SHALL) entregar una lista de las cifras de la memoria que cambian o quedan obsoletas por el cambio de modelo, con el valor anterior, el valor nuevo (o «no medido»), la medida del inventario de la que sale y la ruta de la evidencia. La lista NO DEBE (SHALL NOT) copiar el texto de la memoria al repositorio ni modificar el documento compartido; la actualización la hacen los responsables de la memoria.

#### Scenario: Cifra sin medida de origen
- **WHEN** una cifra de la lista no se puede enlazar con una medida del inventario
- **THEN** la lista la marca «sin origen verificable» en lugar de darla por válida

#### Scenario: La memoria no entra en Git
- **WHEN** se revisa el diff del cambio
- **THEN** no contiene el texto de la memoria, solo referencias a sus secciones según `docs/memoria/README.md`
