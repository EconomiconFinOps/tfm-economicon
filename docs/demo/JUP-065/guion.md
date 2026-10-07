# Recorrido de demostración — 7 minutos

Audiencia: tutor/equipo. Mensaje: «Economicon permite consultar una muestra de gasto Cloud y contrastar explicaciones con su documentación». Abrir previamente `/login`, `/`, `/assistant` y la ficha de evidencia; evitar terminales con secretos.

| Tiempo | Acción exacta | Qué decir | Resultado esperado / evidencia |
| --- | --- | --- | --- |
| 0:00–0:30 | Presentar el alcance | «Usamos una API Azure simulada con una muestra pública; las respuestas de IA se comprobarán contra fuentes». Identificar proveedor real o mock según el ensayo. | No afirmar acceso a Azure real ni ahorros logrados. |
| 0:30–1:00 | Entrar con la cuenta demo y seleccionar Core Finance (`tenant-core`) | «Cada consulta queda vinculada al cliente seleccionado». | Sesión válida; tenant visible; captura sin credenciales. |
| 1:00–2:15 | En `/`, Mes inicial `2024-06`, Mes final `2024-06`, agrupar por Grupo de recursos | «Seleccionamos junio, pero los datos son una muestra pública, no una factura mensual completa. Conservamos moneda y procedencia». | Total 0,06 USD, 38 registros; ocho grupos, incluyendo DevTestLab unificado. La UI consulta `[2024-06-01, 2024-07-01)`; la carga y referencia fijadas siguen en `[2024-06-01, 2024-06-20)`. En esta muestra coinciden los registros: no hay filas de la suscripción desde el día 20. Contrastar datos y grupos con `costes-esperados.json`; no confundir ambos periodos ni sumar grupos redondeados para recalcular el total. |
| 2:15–2:45 | Cambiar a Growth Ops y volver a Core Finance | «El cliente sin carga debe mostrar ausencia de datos». | Growth sin costes; Core recupera 0,06 USD. Esto comprueba separación visual, no sustituye una prueba de autorización contra tenants ajenos. |
| 2:45–3:15 | Mostrar la evidencia de ingesta ya completada del documento FinOps | «El asistente utiliza este documento versionado». | ID de documento/job/chunks y hash del corpus del ensayo, estado completed. No esperar una indexación larga en directo. |
| 3:15–4:30 | Conversación nueva en `/assistant`; enviar el prompt completo JUP-069-004 de `prompts.json` | «¿Uso coste actual o amortizado para repartir el coste de una reserva?» | Distingue facturación de distribución temporal del compromiso; explica uso del amortizado para showback, sin sumar ambas vistas. Texto exacto variable. |
| 4:30–5:15 | Abrir una cita de esa respuesta | «Podemos revisar en qué se apoya la explicación». | Documento correcto, extracto que respalda la afirmación y referencia resoluble del tenant; repetir tras recarga. Un ID de chunk sin evidencia visible no supera este paso. |
| 5:15–6:15 | Conversación nueva; enviar JUP-069-003 completo | «¿Por qué ha subido tanto el gasto?» | Pide alcance y periodo; propone investigación sin inventar importe, servicio culpable ni causa raíz. |
| 6:15–7:00 | Mostrar límites y cerrar sesión | «Hemos demostrado consulta de muestra y explicación trazable; el ahorro y las decisiones operativas necesitan más evidencia». | Sin promesas de ahorro ni apagado; ruta protegida vuelve al login tras salir. |

## Reserva y ampliación

Si hay dos minutos extra, usar JUP-069-001 en conversación nueva: leer «escenario sintético» antes de pegar el contexto. Esperados: total 1.000 EUR, VM 600 EUR, cuota 60 %, tolerancia 0,01 EUR/puntos porcentuales. No conecta ni carga esos datos en el dashboard. JUP-069-023 y 025 comprueban abstención ante tenant real inaccesible y orden de apagado; conservar el texto y la rúbrica originales.

## Plan ante fallos

- Si login, costes o aislamiento fallan: detener el tramo funcional; registrar el error y pasar a explicar el diseño. No presentar capturas anteriores como resultado actual.
- Si el proveedor tarda más de 30 segundos: anunciar incidencia, esperar como máximo otros 30 segundos y registrar `blocked`; no improvisar múltiples reintentos. Es un límite de presentación propuesto, no un SLA del producto.
- Si aparece 502, no pulsar repetidamente reenviar: existe un residual documentado de duplicación de mensajes en JUP-025. Guardar evidencia y comenzar conversación nueva después de diagnosticar.
- Comprobar que el mensaje va a la conversación nueva seleccionada antes de usar las conversaciones de reserva: JUP-104 reprodujo RF-104-001, que puede devolver la selección a la anterior. Si ocurre, registrar `fail` y detener ese tramo; la preparación no corrige el producto ni declara acreditadas esas reservas.
- Si falta una cita útil, marcar `fail` con servicio operativo o `blocked` por integración pendiente; no sustituirla silenciosamente por la rúbrica.
- Alternativa disponible ahora: guion y referencias offline, etiquetados como preparación. Solo usar vídeo/capturas de un ensayo cuando existan y muestren fecha, commit y modo; hoy no se ha generado ese respaldo.
- Con mock se puede ensayar navegación y errores. No cuenta como ensayo definitivo de IA real. No modificar preguntas, corpus o respuestas esperadas para ocultar un fallo.
