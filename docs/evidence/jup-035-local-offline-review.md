# JUP-035: corte local de evaluación e ingeniería

13/10/2026. Producto base `fc0f4697`; fixtures corregidos `5a2bc473`,
evaluador `41fdca67`. No publicación, despliegue, inferencia ni juez externo.
Este informe es una adjudicación del agente, no una validación humana de la PR.

## Qué queda separado

CD/HMAC está extraído en la rama local `local/JUP-035-cd-hmac`, commit `ba778bb6`,
sobre develop oficial `bfaf3983`:16 pruebas unitarias pasan. No acredita permisos
POSIX ni un despliegue real. Develop no contiene el subsistema de chat: las carreras,
UTF-8 y planificador permanecen sobre la base existente de chat. La corrección
`551fb81` de decisión nativa truncada no es aplicable directamente a develop.

En `local/JUP-035-evaluation` el producto sigue idéntico a `fc0f4697`. Se corrigieron
seis fixtures sin `basis`, conservando comprobaciones;38 pruebas del archivo pasan.
Metadata/operaciones backend:68PASS, con SQLite y fixtures, sin Cockroach real.

## Recibos históricos revisados

Se revisaron todas las44 respuestas completas de las dos full28:253 comprobaciones
de banco y rúbrica transversal, con9 juicios inciertos conservados. Los12 intentos
sin respuesta (5+7) permanecen como fallo técnico, sin calificación semántica.
Los requisitos originales del banco, sus tolerancias y los tres documentos fuente
mantienen sus hashes. No se adjudicaron los focales como sustitutos de la full28.

| Resultado local por respuesta | Primera campaña | Segunda campaña |
| --- | ---: | ---: |
| Pasa banco y rúbrica local |14|12|
| Fallo confirmado en al menos un criterio |5|7|
| Pendiente por juicio incierto sin fallo confirmado |4|2|
| Fallo técnico, sin respuesta |5|7|

La rúbrica transversal añade pertinencia/soporte y consistencia: no se atribuye
al banco original. Una respuesta puede cumplir el banco y fallar por citas o
afirmaciones adicionales. Los estados de esta tabla no son aceptación oficial.

La comparación emparejada registra8 transiciones PASS→FAIL y2 FAIL→PASS por
requisito, además de transiciones con incertidumbre. Las8 regresiones se agrupan
en5 respuestas (003/011/017/021/024), no8 muestras independientes. Cambiaron también
los fallos técnicos; no se descartan. N=1 por campaña impide atribuir causalidad
a una corrección o declarar mejora estable.

Discrepancias relevantes frente a los comentarios históricos:

- 003 segunda: cumple alcance/método del banco, pero sus chunks8/14 no contienen
  todos los pasos que enumera; falta el9. El antiguo NO_VIOLATION_OBSERVED no basta.
- 014 ambas: el cálculo200EUR/20% es correcto; rules:5 no respalda las afirmaciones
  concretas de la respuesta. Se registra aparte de números/cobertura.
- 018 ambas: cálculo y límite estricto correctos; cita rules:6 sobrante.
- 021 primera:80EUR/mes y40% correctos; contradicción adicional70 frente a93,33.
  Segunda: desaparece esa contradicción, pero las citas son improcedentes y el
  signo de la variación adicional46,67% queda incierto por su redacción.
- 008: fórmulas y división por cero correctas; falta adjudicar soporte/pertinencia.
  En la segunda, «unallocated son0EUR» y «no significa que ... sea cero» necesitan
  distinguir el escenario hipotético de una afirmación sobre costes reales.

Se conservan incertidumbres adicionales en004/014/019/023/025. No se resolvieron
para mejorar artificialmente la tasa ni se ajustaron reglas a los casos reservados.

## Reserva y reproducibilidad

Se congeló scorer/rúbrica/partición y adjudicaciones de calibración antes de revisar
013–015 y020–022. Se mantienen familias completas en reserva entre ambas campañas.
No es un conjunto ciego nuevo: los resultados históricos eran conocidos. Se usó
la misma rúbrica sin entrenar juez. No procede publicar sensibilidad/especificidad
de un juez que no existe ni llamar calibrada a una heurística por coincidir aquí.

Herramienta y comandos: [evaluación de recibos](../validation/JUP-035-receipt-evaluation.md).
El evaluador tiene11 pruebas PASS. Los textos/juicios permanecen fuera de Git en
el directorio hermano `materiales/07-evidencias/PR121-local-evaluation/`:

- `judgments-first.json`, `judgments-second.json`: razones y hashes por requisito.
- `calibration-freeze.json`, `calibration-first.json`, `calibration-second.json`.
- `historical-first.json`, `historical-second.json`, `historical-comparison.json`.
- `offline-evidence-manifest.json`: hashes de artefactos y verificación del corpus.

## Suite técnica completa y límites actuales

Primera ejecución completa processor en Windows con Python3.12 nativo y paquetes
prestados por PYTHONPATH: **1454PASS/13FAIL/4ERROR/96SKIP** en400,51s.
Se conserva `full-processor.log`; no se presenta como verde.

- Diez incidencias corresponden a subprocesos que eliminan/sustituyen PYTHONPATH
  y pierden dependencias (incluido uvicorn). Repetición de los dos archivos con
  el intérprete del entorno virtual: **10PASS/6SKIP**, sin modificar código.
- Dos casos de enlaces simbólicos fallan por WinError1314. No se redujeron sus
  aserciones ni se concedieron privilegios globales para ocultarlo.
- Cinco casos de resumen/capacidad/cancelación fallan. Un caso se reproduce aislado:
  antes de recibir cabeceras existe socket propio, shutdown devuelve éxito, pero
  el trabajador no termina en los2s exigidos. Causa/plataforma aún no resueltas;
  evidencia `cancel-diagnostic.log` y `cancel-shutdown.log`. No llamarlo ruido.

Docker Desktop local no tiene daemon accesible y WSL no enumera distribuciones
instaladas; contexto Docker predeterminado apunta a DockerServer compartido.
No se ha usado ese servidor para desplegar una nueva base. **N=3/N=5 NOT_RUN**;
sin base repetida no se inicia otra serie de parches semánticos. Gasto nuevo0;
último acumulado confirmado0,957927619USD, techo2USD.

## Trabajo aún pendiente

Diagnosticar/corregir la cancelación conservando propiedad del trabajador y
capacidad; contrastar Linux cuando exista entorno local viable. Preparar medición
repetida reproducible para la base exacta y cerrar el informe de entrega con sus
limitaciones. Acuerdo de criterios y estrategia de integración corresponde a
revisores/equipo; no se ha contactado con ellos ni cambiado las PR remotas.
