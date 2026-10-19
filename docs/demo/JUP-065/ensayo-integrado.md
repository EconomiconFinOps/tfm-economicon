# Procedimiento del ensayo integrado JUP-065

Actualizado el 15/10/2026; **no ejecutado**. Complementa el [preflight](preflight.md),
el [guion](guion.md) y la [plantilla de evidencia](registro-ensayo.md).
La preparación offline puede comprobarse ahora; el ensayo final requiere el MVP
integrado. Ninguna prueba mock acredita generación, calidad ni aceptación humana.

## Puertas de entrada

| Requisito | Qué debe registrarse antes de ejecutar | Estado de esta preparación |
| --- | --- | --- |
| A / JUP-122 (JUP-035) | SHA integrado, dictámenes y arranque HMAC/migración | PR130 integrada en cf821570; no acredita calidad de B |
| B / JUP-123 (JUP-035) | SHA aceptado e integrado, criterios/evaluación y citas/modelo real comprobados; autorización de activación | Pendiente de aceptación e integración; CHAT_ENABLED=false por defecto |
| JUP-036 | SHA integrado, contrato y ejemplo aceptado de ámbito/periodo para consultar costes, dictámenes de sus responsables | PR69 integrada en 53b43bb1 y Trello Hecho el 15/10; falta ensayo combinado |
| Preparación JUP-065 | SHA de PR63, integridad de 15 artefactos y checks, revisión Paris y validación Víctor del incremento | f27eb7f validado por Víctor y aprobado por Paris; el incremento actual necesita revalidación |
| Pairing | Nota del trabajo conjunto de Lucía o reasignación explícitamente acordada y reflejada en Trello y PR | Pendiente; ninguna excepción de otras tareas se aplica |
| Entorno y proveedor | Instancia propia, autorización de ejecución/consumo, credenciales por canal seguro, versiones y puertos | Pendiente; este trabajo no despliega ni consume modelos de pago |
| Datos e índice | Core sólo con muestra fijada, Growth vacío, corpus permitido y embeddings/modelo/dimensión compatibles | Referencias preparadas; carga y comprobación futuras |

No basta una tarea en Hecho, una URL que responda o un gate verde: comprobar el
recorrido sobre el mismo SHA/entorno que se va a presentar. Si falta una puerta,
marcar `blocked` en una copia del registro, con dependencia y siguiente acción.
No rellenar la plantilla canónica ni aceptar el ensayo por analogía con otro.

## Secuencia de ejecución y resultados esperados

1. Copiar `registro-ensayo.md` fuera de `generado/`; fijar identidad completa del
   entorno y del paquete. Ejecutar los tres comandos del README antes de cualquier
   regeneración. Esperado: 15 reproducibles, tests de integridad correctos, 28 consultas.
2. Aplicar preflight §1; servicios saludables y navegador sin bypass de CORS.
   Registrar SHA/imágenes, hora y recibo sanitizado. Un proveedor mock sólo sirve
   para un recorrido parcial identificado; el ensayo generativo queda bloqueado.
3. Cargar y repetir exactamente preflight §2: 38 registros, cuatro páginas, mismo
   run_id, ocho grupos y 0,06 USD. Guardar ambos recibos y billing Core/Growth.
   La API Azure es simulada y el CSV es una muestra pública, no gasto del cliente.
4. Indexar una vez cada documento permitido según §3; guardar IDs y consulta SQL
   que demuestra `completed`. Registrar configuración y hash de corpus/índice.
   Mantener rúbricas y respuestas esperadas fuera del contexto enviado al modelo.
5. Con A y B aceptadas y el panel activado según preflight §1/§3, recorrer el guion de siete minutos y guardar respuestas originales, citas,
   capturas y tiempos. JUP-069-004 debe explicar actual/amortizado con fuente
   pertinente; 003 debe pedir contexto sin inventar una causa. Abrir cita y
   recargar conversación. Contrastar cada criterio de las rúbricas privadas.
6. Ejecutar reservas 001/023/025 en conversaciones nuevas durante preflight:
   1.000 EUR/600 EUR/60 % son sintéticos; no mostrarlos como billing. Verificar
   abstención ante tenant ajeno y orden de apagado sin ejecutar acciones.
7. Ejecutar el [tramo JUP-036 del guion ampliado](guion.md), también en el ensayo técnico del guion corto. JUP-036 está integrada; ejecutar el tramo separado en la ruta `/assistant`,
   modo de costes Azure (no el panel generativo): Core, suscripción
   `64e355d7-997c-491d-b0c1-8414dccfcf42`, intervalo explícito
   `[2024-06-01, 2024-06-20)`, tipo ActualCost, moneda USD. Usar el contrato y
   controles publicados por JUP-036, sin inventar endpoint ni suponer análisis
   libre del lenguaje. Comparar total con billing (0,06 USD) y ámbito/periodo
   de la evidencia. Si el contrato sólo admite meses, usar junio completo y
   documentar por qué contiene las mismas 40 filas. Comprobar Growth sin datos.
   Un resultado estructurado correcto no demuestra redacción por un modelo;
   si se presenta como respuesta generativa, adjuntar además traza segura de
   JUP-035 A/B. No alterar los cinco prompts fijados para introducir este caso.
8. Verificar logout/rutas protegidas, registrar incidencias y repetir los pasos
   afectados tras corregirlas. Otra persona reproduce el recorrido en una
   ejecución identificada. Aplicar controles de 30 y 5 minutos del preflight.

## Decisión y evidencia mínima

Cada paso lleva resultado observado, enlace a recibo/captura, autor y fecha;
cada caso de IA conserva entrada, respuesta, cita, rúbrica y latencia. La
evidencia histórica de Víctor sobre `bf50073`/`b77d596` es de runtime parcial
con mock; sirve como antecedente, no acredita la combinación actual ni IA real.
Los hashes intactos permiten reutilizar comprobaciones offline con su SHA y
fecha; no permiten trasladar navegación, proveedor, tiempos ni aceptación.

Propuesta operativa: pasos principales `pass`, sin fallos/bloqueos/pendientes,
siete minutos objetivo (hasta nueve con reserva) y reproducción independiente.
El tramo JUP-036 tiene duración separada hasta acordar su lugar en la presentación.
El equipo debe confirmar esta propuesta y documentar cualquier limitación aceptada;
no sustituye los criterios de la tarjeta ni la evaluación completa JUP-069/070.

Alejandro conserva liderazgo, Lucía pairing, Paris revisión y Víctor validación.
Publicar las dos reviews según CONTRIBUTING, sobre el alcance efectivamente
comprobado, y enlazar evidencia en Trello mediante la integración autorizada.
La decisión de aceptación queda pendiente; esta preparación no hace merge,
no cierra JUP-065 y no acredita aprobaciones ni participación inexistentes.
