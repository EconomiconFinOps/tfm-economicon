# Diseño del colector independiente — JUP-123

JUP: JUP-123
Trello: https://trello.com/c/TqtcumIN

Se copian bloques autosuficientes desde B, no commits ni árboles de aplicaciones.
El colector sólo recibe un callback GET. El adaptador importa una copia local de
confianza del evaluador JUP-071, que conserva autoridad sobre banco y rúbricas;
no se copia su rama a develop ni se sustituye su transporte de generación.

El plan inmoviliza 29 casos, N1/3/5, prompts exactos, commit y hashes normalizados
como los de JUP-071. Cada muestra tiene conversación y operación exclusivas. El
directorio nuevo contiene originales antes de cualquier suplemento, vistas
derivadas y manifiesto. Un snapshot de RAG sólo se acepta cuando coincide
exactamente con el hash y los IDs del manifest registrado por el servidor.

La exportación verifica otra vez los recursos originales y la evidencia;
un fallo de transporte o recogida incompleta se traduce en blocked del scorer de JUP-071,
una muestra ausente sigue ausente. No hay evaluador semántico nuevo. La evidencia
completa está en public_evidence y sidecars; no se inventan distancias para el
campo legado retrieved. Si un fragmento de corpus carece de distancia medida,
la exportación queda bloqueada aunque la recogida esté verificada. A no entrega
esa distancia: puntuar esas filas exige que JUP-071 adapte su evaluador para
usar public_evidence, fuera de este cambio. Procedencia local y declaraciones del operador no
atestiguan el runtime ni el proveedor. Cada repetición conserva su identidad;
reexportar no crea una nueva ejecución.

La autorización actual no requiere inferencias: se valida con 33 pruebas offline
y la suite JUP-071 real contra un servidor local simulado. La integración con un
despliegue de A y los juicios independientes quedan para sus responsables.
