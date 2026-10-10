# Diseño JUP-037

Base `origin/develop` c2995a118d419dfe725247bac9c6f219a3f0ea77, 10/10/2026.
El diseño reutiliza el refinamiento local del 03/10 y lo actualiza al encargo
de implementación. Selección explícita en vez de parser libre, como JUP-036.

`OwnershipSelection` prohíbe campos extra. Bearer, tenant y conversación se
autorizan antes de leer billing. `project` agrupa proyecto; las demás dimensiones
agrupan tags canónicos. Moneda/valor seleccionan resultados exactos por grupo sin
sumar cifras redondeadas. Contexto y coste sin dimensión permanecen separados.

El repositorio añade `include_provenance=False`: por defecto devuelve exactamente
billing v2; activado añade IDs de ingesta y días desde el mismo snapshot SQL.
La respuesta persiste un hash por tenant/selección/versión/resultado y conserva
la procedencia. No usa citas documentales para justificar cifras.

Datos ausentes no permiten inferir capacidad de fuente; se comunica desconocida.
Application y owner pueden probarse con fixtures pero su disponibilidad real
sigue pendiente. Catálogos JUP-015 no se inventan. Ver contrato completo en
`docs/api/ownership-questions.md`, incluidos estados, límites e integración futura
con JUP-036. Riesgo residual: límite de evidencia posterior a agregación SQL.

Roles registrados: Alejandro liderazgo, Lucia pairing, Paris revisión, Victor
validación. Desarrollo automatizado no acredita ninguna participación humana.
