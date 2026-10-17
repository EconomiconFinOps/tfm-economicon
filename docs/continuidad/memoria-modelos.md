# Memoria: análisis y elección de modelos

Verificado: 2026-10-17. Origen: chat `01a1270c-e332-7462-9c90-706d49ade92c`.
Encargo humano: analizar modelos, justificar el elegido, preparar material para
la memoria y abrir una JUP sólo si resulta necesaria.

## Actualización de validación — 17/10/2026

Continuación posterior autorizada: los smokes separados DeepSeek/DeepInfraFP8 y
MistralLarge4/ZDR devolvieron HTTP200. El arnés rechazó footers SSE vacíos;
replay con consumidor d965 y esquema real acepta ambos drafts y rechaza el
contrafactual con texto posterior. Evidencia `B-assisted-validation-route-smoke-v4-replay-20261017-v1.json`
SHA6c17c5d0, sin nuevas respuestas pagadas para el replay. Esto demuestra sólo
compatibilidad del borrador guardado, no calidad, fase final, API ni N5.
Nueva N5 DeepInfra separada del CoreWeave histórico (plan a12e5d1a) activa desde
11:34:41UTC, PID99133/start4887333, primeras operaciones API completas y coste
observado, sin juicio semántico final ni aceptación. La comparación histórica
no se reetiqueta. Elección de esta ruta para mantener modelo/FP8 y evitar la
limitación CoreWeave observada; no demuestra superioridad general o causalidad.

Petición humana posterior: localizar otro modelo compatible para evitar429.
Investigación pública de470modelos y catálogo ZDR, sin inferencias/gasto/envío
de corpus/cambio de gateway. Shortlist `B-model-alternatives-20261017-v1.json`
SHAac41b83c ysu informe.md en la evidencia externa. Las cuatro rutas anuncian
JSONSchema/temperature/max_tokens/reasoning y contexto suficiente:
DeepSeekV4.1Flash/DeepInfraFP8(.14/.42USDporM), el mismo porNebiusFP8(.30/1.20),
MistralLarge4/mistral-zdr(.68/2.09) yMiniMaxM3/Together(.30/1.20).
Recomendación para reducir cambios: probar primero DeepSeek porDeepInfraFP8;
modelo distinto preferido para prueba: MistralLarge4, con reasoning_effort=none
documentado. MiniMax mantiene pendiente confirmar razonamiento desactivado.
No hay compatibilidad de ejecución/semántica demostrada: catálogo100% no garantiza
inferencia, strict/streaming reales deben probarse en una campaña separada.
No se altera la elección histórica ni su comparación; nuevo candidato no activado.
N5actual95(91conformes/4técnicas),45pendientes y todas reservas preservadas.

El párrafo siguiente conserva el corte093 anterior a los429de010/011:
La comparación e informe del16/10 siguen congelados; no se reescriben sus cifras.
El candidato posterior d965 conserva N5 NUEVA140:93recogidas,91conformes538checks,
2técnicas(008r4:4timeouts;009r4:HTTP404),11noevaluables/47sin despachar. Paquete093
230archivos/manifest82517598; N3a7 e informecomparativo históricos intactos.
Catálogo público OpenRouter/CoreWeaveFP8 a16oct23:01UTC:status-5/uptime5m0%,30m16.67%.
Indisponibilidad externa observada, no causa única del008 ni fallo semántico probado.
V9/V10terminales/runtimeaparcado; no inferencias hasta disponibilidad fresca. Dos
máximos0.0889632 íntegros; total desconocido14.16844690USD, no gasto cero.
C1/C3acordados yC2asistido autorizado; no aceptación138+2como140éxitos. Hardware
8→24GB/backend512→768MiB impide atribuir latencias sólo almodelo. B local.
Detalles/proofs en evaluación local; no reescribir comparación congelada.

## Resultado y razón

DeepSeek V4.1 Flash/CoreWeave FP8 elegido para el candidato LOCAL B a7f9502d.
La comparación común antigua favorecía GLM (82 conformes frente a 77), aunque
GLM tenía un fallo obligatorio. DeepSeek costó 49,3 % menos y tuvo menor latencia
de generación. Después, la API GLM del candidato corregido quedó en parcial4
por 429; DeepSeek completó 84/84 conformes localmente y 495 comprobaciones.
No se atribuye el salto al modelo: cambian código/corpus/recorrido. Sonnet/Sol
son parciales técnicas; tres respuestas Sol no adjudicadas no son tres aciertos.

No JUP nueva: JUP-063 ya cubre e/g y JUP-109 cubre h. Se mantienen responsables,
lista, fechas y estado. JUP-123 conserva evidencias del producto. No Done.

## Entregables y comprobación

- [Registro técnico](../evidence/JUP-063-model-selection.md) con fuentes y límites.
- [ADR-0022](../adr/ADR-0022-chat-model-selection.md), Proposed: no cambia el
  gateway compartido ni sustituye ADR-0002 aceptado; V4 Pro no es V4.1 Flash.
- Fuera de Git: `../materiales/07-evidencias/PR121-local-evaluation/tfm-model-analysis-20261016-v1.{md,json}`.
- Propuesta nueva e/g/h: `../materiales/06-entregables/JUP-063-modelos/propuesta-modelos-2026-10-16.md`.
  P1–P7/T1, fuentes y cobertura del guion oficial leído por nombre en Drive.
- Manifiesto: misma carpeta de entregables, `manifiesto-2026-10-16.json`.
- Operador offline: `build-tfm-model-analysis-v1.py`; 14 fuentes por hash,
  snapshots/revisiones y paquetes 203+185 verificados. Costes con Decimal.

No se leyó o modificó la memoria compartida ni se copiaron exportaciones a Git.
El texto es propuesta para revisar e incorporar, no una segunda fuente canónica.
No inferencias, claves, reservas o despliegues nuevos. Cota histórica al cierre
21,448811463/30 USD con 13,99052050 USD de reservas íntegras; no factura.

## Pendientes

Revisión e incorporación por liderazgo de JUP-063 (París) y JUP-109 (Lucía),
sin atribuir reviews realizadas; ajuste al máximo global de 20 páginas y nueva
exportación con hashes. CriteriosC1/C3 acordados y C2asistido por excepción humana; recogida/cierre de
N5d965 pendientes. No juez calibrado o conjunto ciego. B sigue local.
Para cifras de campañas, ver [evaluación local](chat-evaluacion-local.md).

## Cierre de preparación — 16/10/2026

Manifiesto SHA `a3ada6275f39c07bef9dd47f14f1568f67a63dae58ef71f4bc7e3e8d8c23d7b4`;
propuesta SHA `12c0f587256c9d344abd377a0f7a7b655cbfb4dbd6af0ff4fbab99fe0231e2ff`.
OpenSpec 75 PASS, 23 enlaces y 14 fuentes verificadas. JUP-063/JUP-109 actualizadas
por el puente autorizado, con lectura exacta y metadatos preservados; registro
`tfm-model-analysis-trello-update-v1.json` en la evidencia externa. No JUP nueva.
El registro técnico enlazado conserva los hashes de ambas descripciones y del
informe. Preparación completada; incorporación y aceptación siguen pendientes.

El humano aprobó el texto exacto y destino del resumen para el equipo. Publicado
una sola vez en [Economicon/#general](https://discord.com/channels/1477630870541303861/1477630871627370702/1560728370025730078)
el 16/10/2026 a las 20:57 de París; contenido e identidad verificados en DOM.
La autorización supera el rechazo automático anterior para ese aviso concreto;
no autoriza publicaciones adicionales. Incorporación a la memoria aún pendiente.
