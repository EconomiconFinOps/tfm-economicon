# JUP-035: fuentes y recuperacion correctiva acotada

## Revision y alcance

Trabajo local autorizado sobre `codex/JUP-035-checkpoint-handoff`, base
`b89509d0d5327634f7bea587dd746a93ae063a0d`. Sin commit, push, publicacion ni merge.
Se preservan los cuatro cambios previos, incluidos la fixture SQL y su informe.
Esta entrega no es una revision independiente ni una aceptacion completa.

## Cambios

- El esquema exige metricas y recomendaciones vacias en estados no accionables.
  Las abstenciones y rechazos pueden seleccionar evidencia documental.
- Los segmentos privados de texto distinguen base documental y no documental.
  Se comprueban pertenencia, pasaje literal y referencias seleccionadas; tambien
  se rechazan fuentes seleccionadas sin uso. Expresiones y clasificaciones
  conservan sus propias fuentes. Esto no demuestra pertinencia semantica.
- Backend autoriza una sola correccion por operacion para tres codigos cerrados.
  Consume uno de los cuatro intentos, conserva el deadline original de 120 s y
  reutiliza una copia autenticada del contexto recuperado en JSONB existente.
  La extension privada queda vinculada a operacion, propietario e intento.
- No se publican deltas provisionales: solo el texto validado y persistido.
  Durante la correccion se presenta `Revisando respuesta`. El error final
  conserva el icono de reintento y no guarda una respuesta rechazada.
- Se contabiliza el consumo comunicado de los intentos, incluidos rechazos y
  truncaciones. Un consumo desconocido permanece desconocido, no se inventa cero.
  Se mantiene la contabilidad externa del gateway para cerrar el gasto total.

## Pruebas locales

Resultados sobre archivos locales, sin llamadas a modelos:

| Grupo | Resultado |
| --- | --- |
| Backend: operaciones, correccion, observacion y seleccion de evidencia | 57 pasan, 0 omitidas |
| Processor: gateway, recuperacion, expresiones, cantidades, recursos, canal privado y respaldo | 161 pasan, 0 omitidas |
| Frontend: presentacion, sesion, recuperacion y panel | 37 pasan |
| Typecheck y construccion frontend | Favorables; aviso previo de bundle grande conservado |
| Mutaciones: fuente sin uso, firma de cache y ampliacion del deadline | Las tres detectadas |

Se conservaron Red, fallos de preparacion y ejecuciones intermedias. La prueba
de consumo reprodujo `usage=None` ante una truncacion antes de la correccion.
Hay controles de cancelacion durante la correccion, segundo fallo definitivo,
presupuesto de cuatro intentos, deadline agotado, cache alterada/ajena, recuperacion
desde un repositorio reinstanciado y limite de contexto incluida la instruccion.
Reinstanciar el repositorio no equivale a ensayar todos los puntos de caida de Docker.
No se repitio la suite SQL del resumen ni la bateria de 28 preguntas.

Reproduccion focal desde entornos Python con las dependencias fijadas del servicio:

```sh
# En apps/backend
python -m pytest tests/test_chat_operations_jup035.py tests/test_chat_correction_jup035.py tests/test_chat_observer_jup035.py tests/test_chat_evidence_selection_jup035.py -q
# En apps/processor, con tokenizer aprobado disponible
python -m pytest tests/test_chat_gateway_jup035.py tests/test_chat_auto_jup035.py tests/test_chat_expressions_jup035.py tests/test_chat_document_quantities_jup035.py tests/test_chat_resources_jup035.py tests/test_chat_private_jup035.py tests/test_chat_grounding_correction_jup035.py -q
```

OpenSpec estricto, trazabilidad y limpieza se ejecutan con los comandos del
repositorio. Los recibos originales conservan comandos, salidas y hashes.

## Ensayos reales

Solo 003, 011, 025 y 026, con conversaciones nuevas y captura SSE/historial.
Todos terminaron y conservaron una pareja usuario-respuesta, con texto emitido
igual al resultado y al historial. `completed` no implica aceptacion funcional.

| Caso | Resultado y limite |
| --- | --- |
| 003 | Dos intentos; la correccion elimina evidencia sin uso. Abstencion financiera coherente. Pendiente: cita el inicio del metodo (chunk 8), pero los pasos completos estan en chunk 9, recuperado y no citado. |
| 011 | Un intento, calculo 100/(100+900)=10 % correcto y sin rechazo contractual. Pendiente: un supuesto dice 10 EUR de total en lugar de 1000 EUR. No se acepta el contenido completo. |
| 025 | Rechazo correcto con fuentes sobre capacidades del MVP y recomendaciones no automaticas. Repeticion limpia: un intento, `refused`, metricas/recomendaciones vacias, citas pertinentes y persistencia correcta. |
| 026 | Dos intentos con una correccion; explica que ingesta incompleta y cero registros no acreditan coste cero. Sin fuentes de relleno, sin cifras inventadas y con persistencia correcta. |

003 y 026 reutilizaron el contexto para la correccion. No se envio el borrador
rechazado como instrucciones. El respaldo parcial de 003 y el supuesto de 011
no son errores detectables mediante la pertenencia/literalidad implementadas.
No se anadio un evaluador semantico ni otro reintento para ocultarlos.

Incidencia del ensayo: la primera ejecucion de 025 se inicio unos segundos antes
de acabar 011 y recibio 429; no se atribuye al producto. Se anadio al ejecutor
una comprobacion de operaciones activas y se repitio solo 025 sin solapamiento.
Se conserva tambien un fallo de preparacion del subdirectorio de esa repeticion,
anterior a cualquier llamada al modelo. La segunda preparacion ejecuto 025 bien.

## Imagenes y presentacion

Imagenes finales construidas y saludables en el stack aislado:

- Backend: `sha256:a050b735c1ab139ccc09c469b8e001390558367ae5026276b6a0187146374234`.
- Processor: `sha256:b0ff2a425b0cd04fa91b793ed62a53d1230db1fcf6f1080271cbb493767a037a`.
- Frontend: `sha256:e4a76575cbf604900f0d5f4596b0a38cbf6b95116ce7e6cdafcf8d2335585a01`.
- Prompt: `jup-035.chat.v3:3bffcd854c1c220bb49f39268abe47bb1dc4bfb2b8ea05f735f3c273c57b771b`.
- Contrato assembler: `f3fb44ad5dd0fdf87cf68ec56200690f40253e1e418db8f5b02ac69c284e3f1b`.

La primera ronda uso las imagenes registradas en `after-recreate.json`.
Despues solo se corrigio la conservacion de consumo en caminos de error del
backend y se ampliaron pruebas; no cambiaron prompt, esquema ni renderer.
025 se repitio sobre las imagenes finales. No se presenta a 003/011/026 como
una nueva ejecucion sobre esas imagenes finales.

Navegador: fuentes pequenas visibles al reabrir 003; 026 recupera respuesta sin
fuentes de relleno; un fallo historico muestra aviso e icono de reintento.
La pestaña original no capturaba imagenes; una nueva pestaña autorizada permitio
guardar ambas capturas, sin pulsar reintento ni consumir IA. Progreso y ocultacion
del borrador estan cubiertos por eventos reales y pruebas de componentes; no se
capturo visualmente en directo el instante de correccion de 003/026.

## Presupuesto y pendientes

Cierre asentado de campana: **0,0936416575 USD**, frente a **0,0714194425 USD**
previos: incremento **0,022222215 USD**. Incluye los intentos rechazados y la
repeticion de 025. Se uso un techo operativo conservador de 0,45 USD dentro de
los 0,50 EUR autorizados. No se cambiaron topes ni caducidad de claves.

Recibos y diff se conservan en el paquete local de esta entrega, identificado
como `jup035-bounded-correction-20261013`, con inventario SHA256. No se incorporan
credenciales ni respuestas rechazadas a Git. Los recibos de aceptacion conservan
las respuestas sinteticas aceptadas y los eventos tecnicos.

Pendientes: contenido/citas de 003 y supuesto de 011; aceptacion integral no
declarada. La revision independiente, validacion humana y publicaciones siguen
separadas. No repetir una bateria completa para estos pendientes.
