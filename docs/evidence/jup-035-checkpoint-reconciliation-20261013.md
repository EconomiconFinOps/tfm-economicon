# JUP-035: correcciones de reconciliacion del checkpoint

Fecha: 2026-10-13. Rama: `codex/JUP-035-checkpoint-handoff`.
Base de estas correcciones: `8d98ae57853c8c24a3d7f61881887b8467fac828`.
Develop incorporado: `bfaf39839718e325eeae7bccf5786d217263b0ea`.
Las correcciones descritas aqui son locales y posteriores al commit de merge.

## Cambios

- Las dos migraciones con prefijo 002 usan sus nombres completos como claves
  independientes. Un marcador historico 002 no impide ejecutar los pasos
  idempotentes de ninguna. La verificacion conserva la comprobacion del esquema
  y acepta el marcador antiguo o el nuevo identificador del chat.
- La vista de propiedad envia siempre ownership_query; ya no ofrece una
  modalidad que el backend rechaza con legacy_chat_retired.
- El panel de anomalias registra filas visibles, filtros, monedas y estados
  de carga/error. Los datos sinteticos se marcan como simulated. No se
  incluyen autores ni motivos libres del detalle, ni se convierten impactos
  de pantalla en evidencia financiera verificada.
- Las pruebas de sesion y aislamiento conservan la cobertura de develop con
  sus textos en espanol y la ruta de propiedad separada del chat.
- Las pruebas de CSV leen el Blob mediante FileReader, manteniendo las
  comprobaciones de formulas neutralizadas y valores exactos.

## Comprobaciones

- Typecheck frontend: correcto.
- Siete suites afectadas: 198 correctas y una expectativa antigua del panel
  de anomalias fallida. Tras actualizar esa expectativa, la suite de capturas
  termina con 12/12 correctas.
- Suite completa frontend: 976 correctas y un fallo de compatibilidad de
  Blob.text en JSDOM. Tras corregir la lectura de la prueba, las cuatro suites
  de CSV, anomalias, conversaciones y propiedad terminan con 57/57 correctas.
  No se presenta esta repeticion focalizada como una nueva ejecucion completa.
- Backend: 128/128 pruebas correctas de colision de migraciones, historial
  canonico, migracion del historial y CORS. SQLite para las fixtures de
  migracion; no equivale a una prueba nativa sobre CockroachDB.
- Build de produccion frontend: correcto, conserva los avisos de bundle
  grande y modulo importado tanto estatica como dinamicamente.
- Diff sin errores de espacio.

## Limites

Docker Desktop no estaba disponible durante estas correcciones. No se ha
repetido el arranque de Compose con CockroachDB ni la bateria OpenRouter.
No se han publicado cambios ni abierto una PR. Los casos reales 005 y 006
conservan el estado pendiente del checkpoint; estas correcciones no los
declaran superados.

## Comprobacion posterior y rectificacion de fixtures

Docker estuvo disponible en la comprobacion posterior. Se conserva arriba
el resultado inicial, incluidas sus limitaciones.

- Frontend completo: 977 pruebas superadas; typecheck y build correctos.
- Azure Cost API: 81 pruebas superadas.
- OpenSpec: 69 elementos validos. Higiene y trazabilidad correctas.
  Workflow CI: 12 pruebas; topologia Docker: 35; gobernanza: 13.
- Backend completo en Linux: 1770 superadas, 136 omitidas y cinco fallidas.
  Tres fallos correspondian a fixtures con el antiguo marcador numerico 002;
  dos eran sensibles a carga y las suites afectadas pasaron al repetirlas
  sin esa carga (54/54). No se presenta como una nueva suite completa verde.
- Processor completo en Linux: 1211 superadas, 96 omitidas y seis fallidas.
  Los seis subprocesos no encontraban PyJWT por la instalacion temporal del
  entorno de ensayo. Con la instalacion accesible a los subprocesos, como
  en CI, su suite obtuvo seis superadas y seis omitidas; sin cambio de producto.
- Las fixtures conservan ahora las claves completas de migracion. La prueba
  negativa retira el marcador del chat sin retirar el de anomalias.
  Comprobacion final focalizada: 22/22 superadas, cero omitidas, en 13.18 s,
  incluidas las pruebas nativas de CockroachDB.
- Compose mock: servicios saludables, migraciones y repeticion idempotente
  correctas. Comprobados generacion, persistencia de dos mensajes, renombrado,
  borrado y consulta de propiedad por HTTP, sin gasto en modelos.
- Diff sin errores de espacio. Correcciones todavia sin commit ni publicacion.

Revision local asistida: no quedan hallazgos abiertos de esta reconciliacion.
No sustituye una revision humana ni la CI del candidato que se publique.
Las pruebas omitidas permanecen omitidas; no se repitio la bateria real.
Los casos 005 y 006 siguen pendientes del checkpoint.
