JUP: JUP-107
Trello: https://trello.com/c/ADFz3fpR

# Revisión del change jup-107-synthetic-cost-demo

## Resumen

Paquete de demo reproducible sobre los datos sintéticos de JUP-106, en `docs/demo/JUP-107/`: guion de 180 s con un paso opcional de 30 s, preparación y vuelta al estado inicial, tabla de preguntas probables, `esperados.json`, receta de navegador para ejecutar fuera del repositorio y plantilla de registro de ensayo. Una prueba (`scripts/tests/test_synthetic_cost_demo.py`, 40 casos, sin base de datos) ata las cifras a una suma exacta con `Decimal` sobre `build_dataset()` y el texto del guion, de las preguntas y de la preparación a esas cifras; corre en CI con `corepack pnpm synthetic-demo:test`. No cambia `apps/`, la herramienta de JUP-106, el dataset público ni `docs/demo/JUP-065/`.

## Decisiones

- Una sola pantalla (dashboard ejecutivo) con el cliente Growth Ops, de 2026-01 a 2026-06; el mes del importe muy grande queda en un paso opcional aparte (D11) para no aplastar el gráfico.
- El vídeo final no se versiona ni lo genera la herramienta: lo graba el equipo con su voz. La receta puede dejar un vídeo mudo de apoyo fuera del repositorio.
- La receta no carga ni retira datos: `apply` y `remove` son comandos explícitos de la preparación.
- Una ejecución de la receta es **automatizada**: comprueba valores y etiquetas de la interfaz y no dice nada del cronometraje de una persona.
- ADR no aplicable: no hay decisión arquitectónica duradera (documentación, una prueba y un guion de navegador que corre fuera del repositorio).

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm synthetic-demo:test` | 40 pruebas correctas; también en `python:3.12-slim` sin paquetes, como el job de CI |
| `corepack pnpm synthetic-costs:test` | 46 pruebas, 8 omitidas (las de CockroachDB), sin cambios |
| `node --test tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 25 de 25; con control negativo (quitar la línea del CI) el test de CI falla |
| `corepack pnpm openspec:validate` | 53 de 53 |
| `corepack pnpm jup:check -- --change jup-107-synthetic-cost-demo`, `jup:check:all` | correctos |
| `corepack pnpm jup:cleanup:check` | 913 archivos, correcto |
| `git diff --check` | limpio |
| Recorrido real con la receta de navegador (stack `jup107` aislado, commit `c1cc7bd`) | D1 a D11 `pass`; ejecución automatizada |
| Controles positivos de la receta | una cifra de desglose, el hueco de marzo tratado como cero, el porcentaje de la comparación en dólares, importes en pantalla antes de D1 y contraseña incorrecta: fallan nombrando la causa |
| Comprobante por API de la preparación | con datos `data_status: partial`, `EUR 90.00 6`, `USD 35.75 2`; Core Finance y datos retirados, `data_status: empty` |
| Estado final | `remove` repetido (2 ingestas y 10 registros, luego 0), `status` `absent`, stack parado con `down -v` |
| Rutas que no cambian frente a `develop` | `apps/`, `scripts/synthetic_costs.py`, `scripts/tests/test_synthetic_costs.py`, `docs/validation/JUP-106-synthetic-costs.md`, `docs/demo/JUP-065/` |

Mutantes ejecutados sobre copias fuera del repositorio, en cuatro tandas (29, 24, 16 y 10): datos del paquete, textos de la guía, cálculo independiente de la prueba y la receta. Los que sobrevivieron se analizaron: unos eran equivalentes por construcción (reemplazar solo la primera aparición de una palabra que aparece varias veces) y otros delataron comprobaciones débiles (la de temas de las preguntas se hacía sobre todo el texto y no sobre la columna de preguntas), que se corrigieron. Al cierre todos los mutantes se detectan.

## Adversarial Review

Tres pasadas con el agente `adversarial-reviewer`, que recibió solo la ruta del change, base y head y la spec. Los hallazgos se copian sin suavizar; la columna «Resolución» es de quien implementa.

### Pass 1 (head `ddc088c`): `changes-requested`

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | HIGH | La prueba solo ataba `esperados.json` al cálculo exacto; las cifras dichas en el guion, las preguntas y los `say`/`expect` no estaban ligadas a nada | Cada sección del guion debe contener el texto y la duración exactos de su paso; las cantidades de `say`/`expect` y de las preguntas deben salir de las cifras del paso |
| ADV-2 | MEDIUM | La tabla de preguntas no se comprobaba (paso equivocado, fila sin paso) | Cada fila cita un paso, cada tema apunta a su paso y las cantidades salen de las cifras de ese paso |
| ADV-3 | MEDIUM | El orden de los pasos y la declaración sintética solo se comprobaban en el JSON | El guion debe tener los mismos pasos en el mismo orden y la declaración dice «sintétic» |
| ADV-4 | MEDIUM | Las pantallas de datos fijos solo se detectaban por ruta | Los nombres de menú solo pueden aparecer en el paso de límites |
| ADV-5 | MEDIUM | El README decía que solo el dashboard ejecutivo lee costes | Corregido: también `/overview-legacy`; una prueba lo vigila |
| ADV-6 | MEDIUM | `-p` no aísla los puertos del equipo | La preparación avisa de los puertos y del CORS |
| ADV-7 | MEDIUM | La preparación no usaba el resumen de la API | Comprobante por API antes y después, verificado tal cual |
| ADV-8 | MEDIUM | La receta no vigilaba fallos de red ni respuestas de error | Vigila `requestfailed` (salvo las cancelaciones de la propia interfaz) y respuestas ≥ 400 |
| ADV-9 | MEDIUM | Comprobaciones laxas de la receta (190.00 aceptaba 90.00, esperas fijas, sin comprobar el inicio de sesión) | Importes con frontera, espera a red inactiva, comprobación de sesión y etiqueta del selector |
| ADV-10 | MEDIUM | Los controles de «no intercepta / no expone secretos» eran fáciles de esquivar | Más patrones prohibidos y escáner de asignaciones de secretos |
| ADV-11 | LOW | D8 decía en voz alta un importe que la pantalla no muestra | Se quitó del texto hablado |
| ADV-12 | LOW | Pequeñas derivas entre `esperados.json` y `guion.md` | Cubierto por la prueba de ADV-1 |
| ADV-13 | LOW | Sin evidencia de la ejecución automatizada | `docs/evidence/JUP-107-validation.md` |

### Pass 2 (head `e872ffb`): `changes-requested`

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | HIGH | El guion decía que el periodo por defecto «hoy no coincide con los datos»; con la fecha actual (abril a septiembre) es falso | Se quitó toda frase que dependa de la fecha; una prueba rechaza «hoy» |
| ADV-2 | HIGH | La pantalla podía mostrar cifras antes de D1 (el navegador recuerda el cliente) | D1 se hace con Core Finance seleccionado; la preparación lo explica y comprueba por API que Core está vacío; la receta comprueba que no hay importes antes de D1 |
| ADV-3 | MEDIUM | Las cifras sueltas sin unidad de `expect` y de las preguntas no estaban atadas | Toda cifra decimal debe pertenecer a las cifras de su paso |
| ADV-4 | MEDIUM | Nada impedía afirmar un ensayo sin registro | Una prueba rechaza esas afirmaciones fuera de la plantilla de registro |
| ADV-5 | MEDIUM | Las respuestas cualitativas no se verificaban | Frases clave fijadas en D4, D5, D9 y por tema en las respuestas |
| ADV-6 | MEDIUM | La receta no verificaba el hueco del gráfico | Comprueba que el trazo del área se interrumpe |
| ADV-7 a ADV-9 | LOW | Core vacío sin comprobar, falta la variante de PowerShell, contraseña dicha en prosa | Corregidos |

### Pass 3 (head `5270f8c`): `accept`

Sin BLOCKING ni HIGH. Hallazgos: ADV-1 MEDIUM (los literales `ui_contains` no estaban atados a las cifras), ADV-2 MEDIUM (los rótulos «Azure» de la pantalla pueden leerse como contradicción con D1), ADV-3 LOW (la lógica de la receta no está bajo prueba), ADV-4 LOW (D1 no comprobaba el cliente activo), ADV-5 LOW (mutaciones de redacción que sobrevivían) y ADV-6 LOW («puertos fijos» impreciso).

Resolución tras el accept, con prueba y mutantes: ADV-1 (los literales se atan a las cifras y a los periodos), ADV-2 (D1 anuncia los rótulos y hay una pregunta que lo responde), ADV-4 (D1 comprueba que el cliente activo es `tenant-core`), ADV-5 (cautelas fijadas en las preguntas, la preparación y la duración del paso opcional) y ADV-6 («por defecto»). **ADV-3 queda abierto** y se registra como RF-107-001.

### Barrido de patrones

Todo texto duplicado entre `guion.md`, `esperados.json`, `preguntas.md` y `preparacion.md` quedó atado a una prueba (texto exacto, cantidades, frases clave o mensajes reales de la herramienta, que la prueba obtiene ejecutándola con su almacén simulado). Las comprobaciones por subcadena de la receta se endurecieron con fronteras. No hay más afirmaciones que dependan de la fecha del día.

## Riesgos

- La interfaz cambia y el guion queda obsoleto: la receta lo detecta al ejecutarse contra el stack; la CI no ve la interfaz y no se afirma lo contrario.
- La lógica de la receta (`checkFigure` y similares) no tiene pruebas automáticas propias; está cubierta por los controles positivos manuales descritos arriba (RF-107-001).
- No se ha hecho ningún ensayo con una persona presentando: el cronometraje de 180 s es el suma de las duraciones propuestas, no una medida.

## Hallazgos registrados

- RF-107-001 en `openspec/findings/backlog.md`: la lógica de la receta de navegador no está bajo prueba automática. Pendiente de aceptación de Lucia.

## ADR

No aplicable.
