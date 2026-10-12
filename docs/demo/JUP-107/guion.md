# Guion de la demo con datos sintéticos de coste

**Duración total: 180 s** (tres minutos) más un paso opcional de 30 s. Los pasos tienen identificador estable (`D1`...`D11`) para poder enseñar uno solo cuando se responde a una pregunta (ver [preguntas.md](preguntas.md)).

Los costes de esta demo son **datos sintéticos** de JUP-106: no son facturas de Azure, no proceden del dataset público y no deben presentarse como tales. Se enseña una sola pantalla, el dashboard ejecutivo (`/`), con el cliente Growth Ops. Las cifras de cada paso están en [esperados.json](esperados.json) y una prueba comprueba que salen de una suma exacta de los datos.

Antes de empezar, seguir [preparacion.md](preparacion.md) hasta tener los datos cargados y la sesión abierta en el dashboard.

### D1 · Declarar que los datos son sintéticos

- **Duración:** 15 s
- **Acción:** Con la aplicación abierta en el dashboard con Core Finance seleccionado (sin cifras en pantalla), sin tocar nada todavía.
- **Qué decir:** «Todo lo que vais a ver son datos sintéticos de coste, generados por nosotros para probar la aplicación. No son facturas de Azure ni vienen del dataset público, aunque los rótulos de la pantalla digan Azure.»
- **Resultado esperado:** Nada que comprobar en pantalla; el público oye la declaración antes de ver ninguna cifra.

### D2 · Elegir el cliente y el periodo

- **Duración:** 15 s
- **Acción:** Elegir Growth Ops en el selector de cliente. Poner Mes inicial 2026-01 y Mes final 2026-06; el periodo por defecto depende de la fecha, así que se fija siempre antes de leer ninguna cifra.
- **Qué decir:** «Elegimos el cliente Growth Ops y los seis primeros meses de 2026. Los dos meses extremos están incluidos.»
- **Resultado esperado:** Aparece «enero de 2026 – junio de 2026 (UTC)» y los totales EUR y USD del periodo.

### D3 · Desglose por servicio y totales por moneda

- **Duración:** 25 s
- **Acción:** Agrupar por Servicio.
- **Qué decir:** «Hay dos monedas y no se mezclan: 90 euros en seis registros y 35,75 dólares en dos. El desglose separa Compute, Storage, Credits y un grupo sin dimensión.»
- **Resultado esperado:** Total EUR 90.00 (6 registros) y total USD 35.75 (2 registros). Filas EUR: Compute 100.00, Credits -50.00, Storage 30.00 y Sin dimensión 10.00; filas USD: Compute 10.50 y Storage 25.25.

### D4 · Un mes sin datos frente a un mes con cero

- **Duración:** 25 s
- **Acción:** Con la moneda EUR, señalar el gráfico y la tabla de costes mensuales.
- **Qué decir:** «Febrero tiene un cero registrado y marzo no tiene ningún dato: la aplicación no los confunde. El gráfico deja un hueco en marzo en vez de dibujar un cero inventado.»
- **Resultado esperado:** Febrero 0.00 con 1 registro; marzo con «—» y «Sin datos de esta moneda.»; enero 100.00 (2) y abril 40.00 (2).

### D5 · Un crédito y la comparación en euros

- **Duración:** 20 s
- **Acción:** Señalar mayo en la tabla y la comparación en euros.
- **Qué decir:** «Mayo es un crédito, un importe negativo. La comparación usa el primer y el último mes con coste: de enero a mayo bajan 150 euros, un 150 por ciento, porque el último mes es negativo.»
- **Resultado esperado:** Mayo -50.00 (1 registro). «Comparación: mayo de 2026 frente a enero de 2026 · EUR» con variación absoluta -150.00 EUR y porcentual -150.00 %.

### D6 · Cambiar de moneda: la comparación en dólares

- **Duración:** 20 s
- **Acción:** Cambiar el selector de Moneda a USD.
- **Qué decir:** «En dólares la serie es distinta: febrero y junio. De febrero a junio suben 14,75 dólares, un 140,48 por ciento.»
- **Resultado esperado:** Febrero 10.50 (1) y junio 25.25 (1). «Comparación: junio de 2026 frente a febrero de 2026 · USD» con +14.75 USD y +140.48 %.

### D7 · Desglose por etiqueta

- **Duración:** 20 s
- **Acción:** Agrupar por Etiqueta y escribir la clave cost_center.
- **Qué decir:** «Podemos repartir el coste por etiqueta: finance y ops, y lo que no tiene etiqueta queda aparte en vez de perderse.»
- **Resultado esperado:** Etiqueta consultada: cost_center. EUR: finance 100.00 (2), ops -20.00 (3), Sin dimensión 10.00 (1); USD: finance 10.50 y ops 25.25.

### D8 · Lo que queda fuera: el registro sin fecha

- **Duración:** 10 s
- **Acción:** Señalar el aviso amarillo de datos parciales.
- **Qué decir:** «Hay un registro sin fecha. No entra en ningún mes y la aplicación lo avisa en vez de repartirlo.»
- **Resultado esperado:** Aviso «Datos parciales: ... 1 registros sin fecha excluidos». Los totales de D3 no incluyen ese registro; su importe (7.77 EUR) sale del conjunto de datos y no se muestra en pantalla.

### D9 · Aislamiento entre clientes

- **Duración:** 15 s
- **Acción:** Cambiar el selector de cliente a Core Finance y volver a Growth Ops.
- **Qué decir:** «Estos costes pertenecen solo a Growth Ops: al cambiar a Core Finance no aparece ninguno.»
- **Resultado esperado:** Con Core Finance: «Sin datos de costes para este periodo.»; al volver a Growth Ops reaparecen los totales de D2. Esto muestra la separación visual entre clientes; no sustituye una prueba de autorización.

### D10 · Límites de lo que hemos enseñado

- **Duración:** 15 s
- **Acción:** Sin tocar la pantalla.
- **Qué decir:** «Para ser claros con los límites: son datos sintéticos; Anomalías usa datos fijos de la maqueta y no sale de estos costes; y el ahorro potencial no está disponible.»
- **Resultado esperado:** Nada que comprobar en pantalla. Esa pantalla (`/anomalies`) no lee los costes cargados: no abrirla como si los leyera. Coste Detallado, Corte Global y Recomendaciones ya no se publican.

### D11 · Opcional: un importe fuera del rango seguro

- **Duración:** 30 s (opcional, no cuenta en el total)
- **Acción:** Poner Mes inicial y Mes final en 2026-07 y la moneda USD; señalar el aviso y la tabla.
- **Qué decir:** «Julio tiene un importe por encima de lo que un número de JavaScript representa sin perder dígitos. La aplicación no lo dibuja, avisa y conserva el valor exacto en la tabla.»
- **Resultado esperado:** Aviso «Algunos importes superan el límite de representación gráfica. Sus valores exactos permanecen en la tabla.» y julio 9007199254740993.01 (1 registro). No comparar julio con febrero: el porcentaje resultante no es presentable.

## Si algo falla

- Si los totales de D2 o D3 no coinciden con los esperados, detener el recorrido, no improvisar cifras y comprobar con `status` que los datos están cargados (ver preparación).
- Si el periodo por defecto sigue activo, volver a poner Mes inicial 2026-01 y Mes final 2026-06 antes de leer ninguna cifra.
- No presentar capturas anteriores como resultado actual ni abrir pantallas que no leen estos datos para rellenar el tiempo.
