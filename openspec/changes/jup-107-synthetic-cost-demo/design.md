JUP: JUP-107
Trello: https://trello.com/c/ADFz3fpR

## Context

Ver `proposal.md` (por qué y qué cambia) y `specs/synthetic-cost-demo/spec.md` (requisitos).

Estado de partida, comprobado en `develop`:

- Los datos sintéticos de JUP-106 se cargan con `scripts/synthetic_costs.py` (`apply`, `status`, `remove`) en `tenant-growth`. Sus valores esperados están en `docs/validation/JUP-106-synthetic-costs.md` y `build_dataset()` los genera sin base de datos.
- Solo dos pantallas leen `/billing/summary`: el dashboard ejecutivo (`/`) y la vista heredada (`/overview-legacy`). `/operational`, `/cuts`, `/anomalies` y `/recommendations` usan datos fijos del frontend (`apps/frontend/src/data/demo/`). El asistente no consulta costes. Los presupuestos de JUP-029 son solo API.
- El dashboard permite elegir mes inicial y final, agrupar por servicio, suscripción, grupo de recursos, proyecto o etiqueta, elegir moneda y muestra la comparación entre extremos, la tabla mensual y el aviso de datos parciales.
- JUP-065 (PR #63, aún sin integrar) define una demo de siete minutos sobre el dataset público y exige `tenant-growth` sin los datos sintéticos. JUP-104 dejó una receta de navegador que se ejecuta fuera del repositorio, sin interceptar peticiones.
- Contexto de entrega: la defensa es el 29/10 (10 a 20 minutos entre los cuatro integrantes), el candidato de entrega con la demo ensayada es el 20/10 y el ensayo con ronda de preguntas, el 27/10.

## Goals / Non-Goals

**Goals:**

- Una pieza corta que se pueda ensayar, repetir por otra persona y usar de dos maneras: respuesta con hechos en la ronda de preguntas y base de un vídeo.
- Que cada cifra del guion salga de una suma exacta independiente y que una prueba lo vigile.
- Que preparar y deshacer la demo sea explícito y no interfiera con JUP-065 ni JUP-104.

**Non-Goals:**

- Decidir quién presenta, dónde cabe en la defensa o si se usa en directo; eso lo decide el equipo.
- Grabar o versionar el vídeo.
- Añadir pantallas o datos nuevos; si el ensayo detecta que falta algo, se pide en su propia tarjeta.

## Decisions

### 1. Un paquete de documentos en `docs/demo/JUP-107/`

`README.md` (qué es y cómo usarlo), `guion.md`, `preparacion.md`, `preguntas.md`, `esperados.json`, `receta-navegador.md` y `registro-ensayo.md`. Es la misma carpeta base que usa JUP-065 pero en su propio subdirectorio, de modo que no hay solape de ficheros.

Alternativa descartada: ampliar `docs/validation/JUP-106-synthetic-costs.md`. Esa guía es para quien valida costes; una demo tiene otro público, otra duración y otro tono, y mezclarlas haría más difícil mantener las dos.

### 2. El guion usa una sola pantalla y cuenta una historia de seis meses

Solo el dashboard ejecutivo con `tenant-growth`, mes inicial 2026-01 y mes final 2026-06. La historia, en orden: declarar que los datos son sintéticos; cambiar a Growth Ops; agrupar por servicio y mirar la serie en EUR; el hueco de marzo frente al cero de febrero; el crédito de mayo y la comparación de enero a mayo; cambiar la moneda a USD y la comparación de febrero a junio; agrupar por la etiqueta `cost_center`; el aviso de datos parciales por el registro sin fecha; y cerrar con los límites. El importe de julio queda en un paso opcional aparte que muestra la tabla de valores exactos.

Motivo: el importe de julio (unos 9×10¹⁵ USD) aplana el gráfico en USD; terminar en junio mantiene legible la serie. Alternativa descartada: recorrer todo el año, que obliga a explicar un gráfico plano al principio de la demo.

La redacción exacta de las etiquetas de la interfaz se fija al ejecutar el recorrido en el stack aislado y se comprueba con la receta; el guion no se escribe de memoria.

### 3. Valores esperados en JSON, comprobados contra una suma exacta

`esperados.json` contiene, por paso, el periodo, la agrupación, los totales por moneda y mes, los recuentos y las comparaciones. Una prueba en `scripts/tests/test_synthetic_cost_demo.py` importa `build_dataset()` de `scripts/synthetic_costs.py`, suma con `Decimal` y compara cada cifra; también comprueba identificadores únicos de pasos, que la suma de duraciones coincide con el total declarado y no pasa de 240 segundos, que ningún paso principal incluye julio y que cada pregunta de `preguntas.md` apunta a un paso existente. Se ejecuta en CI sin base de datos, con un script `synthetic-demo:test` en el mismo sitio que `synthetic-costs:test`.

Alternativa descartada: extraer las cifras del Markdown. Es frágil y deja pasar un cambio de formato que rompe la comprobación sin avisar.

La prueba lleva un control negativo: se altera un importe y debe fallar nombrando la cifra.

### 4. Receta de navegador fuera del repositorio, sin escribir datos

La receta (Node y `playwright-core`, no dependencias del proyecto) recorre los pasos, lee los valores que muestra la interfaz y los compara con `esperados.json`, y guarda capturas y un vídeo mudo fuera del repositorio. No intercepta peticiones, no escribe la sesión y falla ante un error de página, un error de origen cruzado o un paso incumplido, dejando los siguientes como `not_run`. **No carga ni retira datos**: `apply` y `remove` son comandos explícitos de la preparación, para que ninguna ejecución automática cambie el estado sin que quien la lanza lo vea.

Alternativa descartada: que la receta cargue y retire. Es más cómodo, pero un fallo a mitad dejaría datos cargados en un tenant que otras demos suponen vacío.

### 5. Preparación en un stack aislado y con vuelta al estado inicial

`docker compose -p jup107` con volúmenes nuevos; comprobar que `tenant-growth` no tiene costes; `apply`; `status` y el resumen de la API para el periodo principal frente a `esperados.json`; recorrer la demo; `remove`, un segundo `remove` y el resumen vacío; parar el stack y borrar sus volúmenes. Esto responde a que JUP-065 y JUP-104 suponen `tenant-growth` vacío. La herramienta de JUP-106 ya se niega a cargar si hay datos reales, y la guía lo cita como parada y no como algo a saltar.

### 6. Dos modos de uso con los mismos pasos

El mismo `guion.md` sirve de recorrido continuo (vídeo) y de respaldo para preguntas: cada paso tiene identificador estable (`D1`, `D2`...) y `preguntas.md` dice qué paso enseñar para cada pregunta. No hay un guion distinto por modo.

### 7. Registro de ensayo honesto

`registro-ensayo.md` es una plantilla. La ejecución de la receta en este cambio se registra en la evidencia como ejecución automatizada, con su commit y fecha, y sin afirmar nada sobre cronometraje con una persona. Un ensayo humano se anota solo cuando exista su registro relleno.

### 8. ADR no aplicable

No hay decisión arquitectónica duradera: es documentación, una prueba y un guion de navegador fuera del repositorio.

## Risks / Trade-offs

- [La interfaz cambia y el guion queda obsoleto] → La receta falla si los valores o etiquetas no coinciden; la evidencia fija el commit contra el que se ejecutó, y el guion declara esa fecha.
- [Alguien muestra `/anomalies` o `/recommendations` y parece derivado de los datos] → El guion lo prohíbe como evidencia y lo nombra en la declaración de límites; la tabla de preguntas no lo usa.
- [La demo deja `tenant-growth` con datos y rompe JUP-065] → Stack aislado y `remove` explícito comprobado al final; la guía lo advierte.
- [El importe muy grande aplana el gráfico] → Periodo principal hasta junio y julio como paso opcional con la tabla.
- [El tribunal toma los datos por reales] → Declaración antes de la primera cifra y repetida en el material.
- [La prueba de CI no ve la interfaz] → Lo que no ve la CI lo cubre la receta de navegador, que se ejecuta aparte y se registra como tal. No se afirma que la CI valide la pantalla.
- [Tiempo hasta el 20/10] → El alcance es documentación, una prueba pequeña y un guion de navegador; no hay código de producto.

## Migration Plan

No hay migración. Para revertir, basta retirar `docs/demo/JUP-107/`, la prueba y las líneas añadidas en `package.json`, `ci.yml` y `ci-workflow.test.mjs`.
