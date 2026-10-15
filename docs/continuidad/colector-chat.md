# Colector reutilizable del chat

Verificado:2026-10-15. Origen: usuario solicita extraer el colector de B,
adaptarlo para071 y publicar PR independiente; chat
`01a1270c-e332-7462-9c90-706d49ade92c`.
Tarjetas: [JUP-123](https://trello.com/c/TqtcumIN),
[JUP-071](https://trello.com/c/H0woDubz).

Rama independiente `feat/JUP-123-response-collector`, base develop53b43bb1.
Copia de trabajo propia, sin modificar B ni la rama de071. Se extraen colector
GET y reconciliador RAG de B; se añade adaptador para071, guía, pruebas y CI.
No hay cambios en apps, prompts, bancos, corpus, proveedor ni contabilidad.

31pruebas offline pasan. Con071/81ceafc6 se prueban87fixtures por521GET locales,
tres raw de29casos aceptados por su evaluador original, fallo técnico conservado
y reexportación idéntica. No se prueba calidad, despliegue real o gasto mediante
esas fixtures. [Evidencia](../evidence/JUP-123-collector-validation.md),
[guía](../validation/chat-collector.md),
[OpenSpec](../../openspec/changes/jup-123-chat-collector/proposal.md).

El adaptador necesita una copia local confiable con las herramientas071, aún
ausentes de develop. Generar respuestas requiere el flujo autorizado del chat;
este colector sólo lee operaciones persistidas. RAG no expuesto por API necesita
snapshot exacto; sin él la muestra sigue incompleta. No se inventan distancias,
latencias, juicios o atestaciones. Publicación y reviews deben registrarse tras
confirmación de GitHub; no se ha enviado ningún mensaje Discord.
