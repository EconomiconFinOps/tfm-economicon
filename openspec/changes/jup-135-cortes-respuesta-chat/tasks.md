## 1. Diagnostico
- [x] 1.1 Reproducir el fallo con el stack real y clasificar las causas por regla
- [x] 1.2 Confirmar en navegador por que el envio queda apagado tras el fallo
## 2. Implementacion
- [x] 2.1 Reintentos con temperatura creciente y reintento de `invalid_response` del procesador
- [x] 2.2 Omitir segmentos de interpretacion vacios (procesador y copia del backend)
- [x] 2.3 Omitir la metrica financiera no verificada con limitacion visible
- [x] 2.4 Cargar la memoria al terminar en `failed` o `cancelled`
## 3. Comprobacion
- [x] 3.1 Pruebas focales de procesador, backend y frontend; el test del frontend falla sin el arreglo
- [x] 3.2 Comparar las suites completas con develop sin fallos nuevos
- [x] 3.3 Prueba en navegador con Playwright, con la interfaz de develop y la de la rama
- [x] 3.4 Medicion antes y despues: pantalla financiera, banco de JUP-069 y robustez de JUP-071
- [x] 3.5 Informes cargados en el dashboard de evaluacion sin errores
## 4. Entrega
- [ ] 4.1 Abrir la PR contra develop con las decisiones registradas
- [ ] 4.2 Revision y validacion de otras personas
- [ ] 4.3 Anadir `model_identity` a las dos entradas nuevas del manifiesto cuando se integre la identidad del modelo de JUP-133
