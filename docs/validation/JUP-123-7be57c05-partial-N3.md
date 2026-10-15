# JUP-123: candidato técnico conforme y N3 parcial70/84

Verificado el 15/10/2026. Origen: chat 01a1270c-e332-7462-9c90-706d49ade92c.
**B no está aceptada.** Corte actual70/84 bajo el máximo10USD autorizado el15/10.
Se continuó desde009 conservando el prefijo y todas las reservas. Herramientas
5f32ea08/109PASS en directorio separado; producto/plan intactos. El controladorv4
terminó por caducidad sin iniciar015r3. Se conserva debajo el antecedente8/84.
Detalles en [continuidad](../continuidad/chat-evaluacion-local.md).

## Corte actual — 15/10/2026 08:04 UTC

Continuación autorizada bajo10USD, herramientas5f32ea08/109PASS separadas del
producto7be y del plan original.70 recibos verificados:69 completed/1 failed.
Los ocho iniciales y302 filas anteriores siguen idénticos; no se reenvían fallos.

| Comprobación provisional | Resultado |
| --- | --- |
| Respuestas |63 conformes;3 fallidas;3 inciertas;1 fallo técnico|
| Requisitos |400 conformes;4 fallidos;3 inciertos;6 no evaluables|
| Muestras ausentes |14:015–028r3|
| Costes de esta campaña |66 observados;4 máximos íntegros retenidos|
| Contador global + reservas/seed |2.858366129 +3.201520 =6.059886129/10USD|

No es aceptación independiente ni gasto exacto del trabajo.015r1/r2 omiten
seguimiento/alertas;003r2 añade prerrequisitos no documentados. Incertidumbres
003r3/012r3/023r2 se conservan para adjudicar.013r3 termina failed con diagnóstico
classification_unverified_prose en model_validation, sin candidato exacto ni
campo privado causante conservado; no se atribuye a una frase inventada ni a
la caducidad posterior.017/027 conformes2/2, su tercera repetición aún no existe.

008r1/018r1/013r3/014r3 retienen0.319952 cada uno.014 tiene SDK completo pero
delta de clave contaminado: la diferencia coincide con una fase del013; eso apoya
una hipótesis de cargo tardío, no demuestra atribución exclusiva ni liquida coste.
No se libera ninguna reserva. Las claves caducaron08:02:20UTC;015r3 no se admitió.
Extensión sólo de vigencia solicitada hasta10:02UTC, pendiente y no aplicada.

Snapshot privado287 archivos, manifest
c70c75a6ed9569bafcc8e67f4ba8a6f299431b296d994bebbbfc283f4e638084;
revisión local congelada75 archivos, manifest
23a7d14a6a341ea6eeebf84eafcbf7523f740419ecb0635c61d82cad46272e09.
Conservan todos los originales; exportación sólo de vistas públicas sintéticas.
Detalles y rutas en [continuidad](../continuidad/chat-evaluacion-local.md).
Los cortes inferiores describen el antecedente8/84 y no sustituyen este estado.

## Antecedente técnico y corte8/84

## Código y cobertura técnica

Aplicación congelada 7be57c059ef740ae5f525d98ebe631271144f1fb, base A8ea/develop0543.
Pruebas fba415f2220f5eb8945da75efd0496809e8c0755, sin cambios de aplicación;
archivo SHA d34f355d2e2de156e9dc2e07b238beeb7d835a989b391d0358dc2887025301b9.

- Chat: 1747 identidades conformes: 1689 offline y 58 omisiones cubiertas con bases
  reales. No es una ejecución monolítica sin OOM; los intentos previos se conservan.
- Cockroach: 196 ejecuciones conformes tras sustituir 17 identidades de los dos
  ficheros modificados. Pgvector: 20 conformes;14 son contratos adicionales. No
  sumar estas216 ejecuciones como casos nuevos del chat.
- Frontend: 1354 pruebas conformes; tipos, lint y build conformes.

Los dos fallos SQL originales quedan conservados: expectativa antigua de
metadatos y ventana de preparación/observación del deadline demasiado breve.
La corrección exige generation.question_message_id y HTTP504/summary_deadline,
conserva cierre físico/SQLSTATE/<3s y el fallback independiente real0.35s.
Se repitieron ambos ficheros completos:17 nativas PASS y8 offline(2PASS/6SKIP).
Resto de código/build, AST de helpers importados y JUnit/log SHA contrastados.
Prueba final-7be57c05-testfix-fba415f2-technical-proof.json,
SHA36903ccf52f9469f4ea065d2ff2fadd81e62559815b392e8dac55a41d9c2f4b9.

## Construcción y navegador

Build v7 terminó tres imágenes con hashes internos verificados: backend 114,
processor 103 y frontend 127 ficheros. B activo con 365 hashes de fuente y tokenizer
fijo comprobados, tres servicios saludables, mismas bases de datos y recuentos
de operaciones conservados. Otros despliegues intactos; B sin publicar.

Playwright visible:001/006/007/008 en1280/390px, historial y recarga coinciden
con sus recibos; cero errores y escrituras del asistente. Capturas inspeccionadas.
Sin inferencias desde navegador. No acredita streaming/UI de todo el banco.

## Medición real:8 de84

Mismos banco, corpus, rúbrica y partición. Plan de 84 muestras/365 hashes, SHA
1316e2ffaa2cae57b99fd1ce3c282e972692c24a0f059ac671a1e9139957af52.
OpenRouter/GLM-5.2/DeepInfra-fp4, temperatura0, sin fallback.

Ocho operaciones completadas y verificadas; siete costes conciliados. El008
necesitó dos intentos automáticos; se conservan ambos y sus cuatro fases. No se
reenvió manualmente. Controlador terminado; faltan 76 muestras, incluidos017/027.
Juicio provisional 001–008/r1:8 conformes / 49 requisitos conformes. Frente a c7:
47 pass→pass y2 uncertain→pass en ese subconjunto. No es una tasa N3, adjudicación
independiente ni prueba de ausencia de regresiones globales. Introducciones de
citas redundantes003 y limitaciones repetidas006 siguen como deuda de presentación.

## Conciliación pendiente y máximo de 5 USDUSD

La primera fase final008 terminó en EOF/error500 sin usage completo. La respuesta
posterior correcta no liquida ese consumo. Tres fases tienen recibo OpenRouter;
la restante conserva UUID local y su consulta devuelve400. Sin ID upstream en
metadatos/logs del intervalo; endpoint analítico403 con la clave disponible.
La API de [generaciones](https://openrouter.ai/docs/api/api-reference/generations/get-generation)
necesita ID; [analytics](https://openrouter.ai/docs/api/api-reference/analytics/get-available-analytics-metrics-and-dimensions)
requiere clave de gestión. No se crearon/renovaron claves.

| Concepto, corte1792025397 | USD |
| --- | ---: |
| Contador conservador de cuenta |2.548894402|
| Reservas anteriores retenidas |1.921712|
| Reserva íntegra008 |0.319952|
| Cota conjunta |4.790558402|
| Cota con la siguiente reserva0.319952 |5.110510402|

El contador no es atribución exacta al trabajo. Ni spend0, ID inválido ni contador
estable prueban gratuidad. Parada por conciliación incompleta; el cálculo también
impide otra ejecución con máximo de 5 USD. No se intentó009. Claves hasta 15/10 08:02UTC,
sin renovación. No se libera ninguna reserva.

## Evidencia y continuación

Archivos externos en materiales/07-evidencias/PR121-local-evaluation del workspace:

- candidate-7be57c05-partial8-freeze-proof-v1.json:31 hashes, ocho originales/
  derivados, siete costes, reserva008, plan y copia del ledger de 303 filas. Manifest
  SHAbeebcd2e2a307de1e3dee1d10ce28f27c3f6a62951a350b57b7ade288b543e25.
  Originales privados en DockerServer; sólo vistas públicas derivadas exportadas.
- candidate-7be57c05-local-review-current.json y paired-c7-current.json con el
  mismo prefijo: revisión provisional y comparación, ligadas al hash original.
- candidate-7be57c05-activation-result-v1.json, final-adapter-safety-v7.json con
  mismo prefijo y7be57c05-{first,partial8}-ui-result.json: activación/guardas/UI.
- candidate-7be57c05-pending-accounting-1792025199.json,
  candidate-7be57c05-008r1-upstream-1792025262.json y
  candidate-7be57c05-accounting-identities-1792025477.json: diagnóstico sin gasto.

Siguiente paso: recuperar el recibo contable o una decisión explícita de margen,
conservar la reserva y tratar el coste incompleto de una operación finalmente
completada sin falsear su estado. Después continuar el prefijo desde009. No borrar
recibos, reiniciar campañas ni cambiar producto durante la medición. Pendientes
N3/comparación completas, criterios/adjudicación y N5 según alcance/presupuesto.


## Corrección local posterior del evaluador

Revisión4d3f953eb56946cd1b3145243def261dc2dac5ac: las herramientas pueden conservar
el máximo completo de una operación completed con consumo desconocido. El
comprobante terminal_completed mantiene el estado real y el SHA del recibo;
no se libera dinero ni se altera la compatibilidad con terminal_failure.
Los recursos, resultado, historial, dos estados observados e identidad tienen
que coincidir. Runner/auditor admiten ese registro y mantienen el control de gasto.

109 pruebas de herramientas conformes. Ensayo offline sobre proyección contable
de303 filas/5 planes:302 filas anteriores y todos los importes intactos;008 sigue
completed y conserva0.319952, y009 sigue rechazado con máximo5USD. Pruebas externas
completed-retention-tools-v1.json y completed-retention-real-rehearsal-v1.json.
No se transfirió/aplicó esta revisión al runtime, ledger real o campaña congelada.
No atribuir a este código nuevo los recibos recogidos con7be; cualquier continuación
debe registrar sus herramientas por separado sin cambiar el plan o borrar el prefijo.
La consulta al liderazgo sobre6USD está pendiente y no cambia el CAP efectivo5USD.

Revalidación1792026514: controlador terminal,8recibos/303 filas, mismo contador y
recibo perdido aún no recuperado. Bloqueo por conciliación/margen confirmado;
objetivo automático bloqueado, sin aceptación ni nueva inferencia. Retomar exige
evidencia contable nueva o decisión explícita de máximo, conservando el prefijo.
