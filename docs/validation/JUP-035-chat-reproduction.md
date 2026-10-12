# Repetir las consultas del chat

El panel nuevo y `tools/assistant-eval.py collect` usan generaciones, no la
respuesta de plantilla del endpoint antiguo. Requiere Python 3.12, el Compose
del proyecto preparado siguiendo el README y un usuario del tenant probado.

Las 28 entradas de [JUP-035-chat-inputs.json](JUP-035-chat-inputs.json) reproducen
el contexto y pregunta de [JUP-069](JUP-069-questions.json). Son escenarios
sinteticos aportados como texto por el usuario: no insertan costes ni acreditan
evidencia financiera del servidor. Para comprobar cifras verificadas, cargar
los datos sinteticos documentados y aportar su captura mediante
`screen_context` en la entrada correspondiente. El corpus se ingesta siguiendo
el README; las citas dependen del corpus y modelo realmente configurados.

Con `DEMO_PASSWORD` suministrada fuera de Git, ejecutar desde la raiz:

```text
python tools/assistant-eval.py collect --base-url http://127.0.0.1:8000 --tenant tenant-core --inputs docs/validation/JUP-035-chat-inputs.json --output ../chat-evidence/raw-NEW-RUN.json
python tools/assistant-eval.py review-sheet --raw ../chat-evidence/raw-NEW-RUN.json --output ../chat-evidence/review-NEW-RUN.md
```

Ajustar URL y tenant al entorno; usar una ruta nueva fuera del repositorio
para cada ensayo. La herramienta abre una conversacion por caso, espera estados
terminales y detiene los siguientes si no puede confirmar el fin de una operacion.
No basta que se cierre el streaming. El fichero crudo conserva respuesta,
recuperacion, citas, identificadores e intentos; puede contener texto privado.

En mock no hay gasto, pero no se comprueba el proveedor. En IA, verificar claves,
saldo y presupuesto antes de ejecutar: esta guia no autoriza consumir credito.
La revision de las afirmaciones, unidades y sustento de citas es independiente
del estado `completed`. Las latencias internas no medidas no se consideran cero
real. La evaluacion humana JUP-070 sigue separada.

Los recibos locales de las evidencias historicas son antecedentes conservados,
no dependencias necesarias para repetir estas consultas. Cambios de corpus,
configuracion o modelo deben registrarse: no se promete reproducir palabra por
palabra una salida anterior ni equivalencia con sus capturas de costes.
