JUP: JUP-123

## Why

La entrega A aporta la ingeniería del chat; no acredita la calidad de sus
respuestas. JUP-123 separa la evaluación semántica de esa entrega y conserva
los fallos históricos sin reinterpretar una campaña N=1 como mejora causal.
Trello: https://trello.com/c/TqtcumIN
Dependencia: JUP-122, PR https://github.com/EconomiconFinOps/tfm-economicon/pull/130

## What Changes

- Reconciliar el flujo server-documentation-v4 con la base de ingeniería A.
- Recoger campañas reproducibles y completas del banco original JUP-069.
- Comparar por requisito y repetición, agrupando defectos por respuesta.
- Aplicar correcciones deterministas a cálculos, reglas y evidencia según la
  línea base; separar prompts por modo sólo si las mediciones lo justifican.
- Mantener el chat desactivado por defecto hasta su aceptación.

## Capabilities

### New Capabilities
- `chat-semantic-evaluation`: evidencia repetida, trazabilidad y límites de gasto.

## Impact

Backend, processor y evaluación. Chat desactivado por defecto. La medición por
sí sola no autoriza publicación, merge o activación permanente. El 17/10 el
usuario trasladó expresamente el candidato validado a este chat para continuar
su integración; se prepara una PR separada de #131 y #138 bajo el flujo ordinario.

## Resultado local vigente — 17/10/2026

Producto `f3ec760d3c483e8798df2be32ea90bb901ebe36d`, HEAD documental `800775ef`.
Nueva N5:140 completed/conformes,825 comprobaciones PASS, C1/C3 conformes y
C2 asistido por revisor y validador separados conforme a autorización humana.
DeepSeek V4.1 Flash/DeepInfra FP8, banco1.0.1/corpus54, temperatura0 y razonamiento
desactivado, ZDR sin fallback. Comparación de139 pares semánticos sin regresiones;
fallos y reservas históricos intactos. No aceptación humana oficial ni causalidad.

La reconciliación de integración con develop `1de41b90` requiere verificar la
identidad del producto medido y los controles afectados; no hereda automáticamente
la validación de f3ec760d. No se reabre la campaña ni se cambia el gateway compartido.

## Histórico anterior a la campaña final

Candidato actual **d965e2cd9c0de3cd4b7efaf224841c93a94cd8c8**, sobre integración
53b43/A, tras corregir012 y los defectos de premisas/reglas descubiertos por la
revisión asistida.197identidades nativas por herencia explícita,110variantes,
84esquemas/69renders offline y2builds/224hashes conformes; no son197ejecuciones
nuevas sobre d965 ni una validación de proveedor por replay.

El usuario aceptó C1/C3 y sustituyó C2 por dos subagentes separados. Autorizó una
N5 NUEVA140 de este candidato, plan8af94f71, banco1.0.1/corpus54/DeepSeekCoreWeaveFP8.
Corte17/10:93recogidas/91conformes538checks,2técnicas/11noevaluables/47faltantes;
todavía no N5 completa ni
criterios finales satisfechos. No se rellena con las84N3a7 ni se atribuye la
N5GLM5119 a este producto. Históricos/rubricas/rojos técnicos y semánticos intactos.

Las interrupciones por OOM512MiB, diskstallSQL y comparación de orden de montajes
se conservan; V9/V10pararon porfallos técnicos yrestauraron elentorno. Ruta
CoreWeaveFP8indisponible en catálogo público; V11prepara47desde010r4 con gate
fresco antes delanzar/admitir, sin cambiar la combinación medida. Hardware24GB verificado y nuevos3con
límites768MiB coexisten con antiguos6sanos. No comparación de latencias en entorno
idéntico. Cap30USD/mismasclaves4.5/.1hasta17oct18París, contadores/holdsíntegros;
ningún aumento/renovación inferido del hardware o presupuesto acumulado.

UI histórica de a7/2339 y sus límites se conservan en el informe; no hay nueva
prueba de generación/streaming en navegador de d965. API pública/historial/RAGreal
se recogen con identidad exacta por operación y pruebas nativas de contrato.
Dosfallidas no tienen respuesta adjudicable niRAGinventado y no satisfacenC1/C3.
Auditorfinal6estricto140completed ya noaplica talcual. Quedan47, comparación y
auditoría honesta con fallos/11noevaluables;138+2noequivale140éxitos; no juez calibrado, test ciego o superioridad general.
Detalle y pruebas en `docs/validation/JUP-123-local-review.md` y continuidad.
