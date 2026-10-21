# Comparativa histórica GLM / DeepSeek — replay común

Publicación documental preparada el **18/10/2026** por autorización expresa en
HAL 9000 (`01a1270c-e332-7462-9c90-706d49ade92c`), dentro de JUP-063.
Los resultados son del **16/10/2026, 00:58 Europe/Paris**
(15/10 a22:58UTC). No se ejecutó una nueva campaña para publicarlos.

## Cifras citables para el guion JUP-128

| Modelo y ruta histórica | Respuestas | Conformes locales | Fallidas | Dudosas | Coste observado USD | Generación p50 s | Generación p95 s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM 5.2 / DeepInfra FP4 | 84 | 82 | 2 | 0 | 0.3470654625 | 11.6572 | 22.4291 |
| DeepSeek V4.1 Flash / CoreWeave FP8 | 84 | 77 | 6 | 1 | 0.176012028 | 5.5399 | 9.6628 |

Cada configuración usa **28 casos ×3 repeticiones**, sobre las mismas preguntas
y contextos congelados. Cada respuesta suma draft y final: **168 fases por
configuración**. El coste es la suma informada por el proveedor para esas fases,
con cero costes desconocidos en esta población; excluye reservas históricas y
otros cargos de la cuenta. DeepSeek costó **49,3% menos en este replay común**:
`100 × (1 −0.176012028 /0.3470654625)`. No es ahorro empresarial medido.

Las latencias son percentiles de la suma draft+final por respuesta, en segundos,
con interpolación lineal en `(n−1)×p`. Excluyen inicio, recursos, preflight y
scheduler; no son tiempos API/UI ni latencia extremo a extremo del producto.

Texto breve reutilizable: «En un replay histórico común de84 respuestas por
configuración, GLM obtuvo82 conformes locales y DeepSeek77. DeepSeek tuvo un
coste de generación49,3% menor y menores percentiles de generación en ese
replay. Son resultados provisionales del banco conocido, sin adjudicación
independiente ni aceptación funcional».

## Fuentes y reproducción offline

- [comparison.json](comparison.json): **copia exacta** del informe original,
  SHA-256 `d8dff405f58063c79757d3f29abd290c8015a42bd7b2da0e785205f007e30380`.
  Incluye los84 pares y sus hashes de criterios; no contiene textos de preguntas,
  contextos, respuestas, credenciales ni ledger.
- [phases.csv](phases.csv): proyección explícita de336 recibos originales,
  limitada a modelo/caso/repetición/fase/coste/duración/hash del recibo.
  Permite recalcular costes y percentiles sin publicar las peticiones/respuestas.
- [provenance.json](provenance.json): rutas de modelo/proveedor, cortes UTC,
  hashes de snapshots/reviews/banco/contextos y denominadores. Los originales
  externos permanecen intactos; sus hashes permiten contrastarlos al custodio.
- [manifest.json](manifest.json): identidades de los tres archivos de datos.
- Verificar desde la raíz del repositorio, sin red, contenedores ni inferencia:
  `python docs/evidence/JUP-063/glm-deepseek-20261016/verify.py`.

## Alcance y límites conservados

`PAIRED_LOCAL_PROVISIONAL_COMPARISON`; `acceptance=NOT_ASSESSED`,
`independent_adjudication=false` y `api_ui_validated=false`.
La rúbrica adicional es un juicio local provisional, no una evaluación humana
independiente ni un conjunto de aserciones automáticas del banco.
GLM conserva incluso un fallo obligatorio del banco. Más conformes promedio no
compensan defectos obligatorios, ni prueban superioridad estadística o causal.

La equivalencia declarada tiene una base acotada:56 capturas offline y auditoría
de equivalencia101-schema. No prueba equivalencia universal, runtime actual,
recuperación actual, disponibilidad estable ni comportamiento del proveedor
upstream fuera de la ruta registrada. No se ha vuelto a puntuar semánticamente.

No se agregan a este denominador las parciales Sonnet/Sol, GLM/API con429,
las ejecuciones DeepSeek anteriores fallidas, la N3 corregida posterior o la N5
de140 respuestas con DeepSeek/**DeepInfra**. Son campañas distintas.
La selección documental y su alcance se registran por separado en el
[ADR-0025](../../../adr/ADR-0025-chat-model-selection.md).
Publicar estas cifras no cambia modelo, gateway, presupuesto ni el estado de
aceptación de JUP-063/JUP-109/JUP-123, y no incorpora la memoria canónica.
