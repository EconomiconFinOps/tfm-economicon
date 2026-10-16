# Diseño del colector independiente — JUP-123

JUP: JUP-123
Trello: https://trello.com/c/TqtcumIN

Se copian bloques autosuficientes desde B, no commits ni árboles de aplicaciones.
El colector sólo recibe un callback GET. El adaptador importa una copia local de
confianza del evaluador JUP-071, que conserva autoridad sobre banco y rúbricas;
no se copia su rama a develop ni se sustituye su transporte de generación.

El plan v2 inmoviliza 29 casos, N1/3/5, prompts exactos y hashes normalizados
como los de JUP-071, incluidas métricas y calibrador. El commit queda informativo;
un commit ajeno a esos contenidos no invalida la recogida ni cambia la identidad
harness_commit congelada al exportar. Los planes v1 conservan su contrato anterior.
Cada muestra tiene conversación y operación exclusivas. El
directorio nuevo contiene originales antes de cualquier suplemento, vistas
derivadas y manifiesto. Un snapshot de RAG sólo se acepta cuando coincide
exactamente con el hash y los IDs del manifest registrado por el servidor.

La exportación verifica otra vez los recursos originales y la evidencia;
un fallo de transporte o recogida incompleta se traduce en blocked del scorer de JUP-071,
una muestra ausente sigue ausente. No hay evaluador semántico nuevo. La evidencia
completa está en public_evidence y sidecars; no se inventan distancias para el
campo legado retrieved. Si un fragmento de corpus carece de distancia medida,
la exportación queda bloqueada aunque la recogida esté verificada, salvo cuando
la herramienta importada anuncia exactamente ACCEPTS_UNMEASURED_DISTANCE = True.
Entonces conserva corpus y citas con distance: null; distancias mal formadas
siguen bloqueando. A no entrega esa distancia: JUP-071 debe adaptar su evaluador
antes de anunciar la capacidad, fuera de este cambio. Procedencia local y declaraciones del operador no
atestiguan el runtime ni el proveedor. Cada repetición conserva su identidad;
reexportar no crea una nueva ejecución.

structured exporta sólo status y has_next_actions, sin texto de acciones. Bajo
execution.collection.server_reported, cada muestra conserva los metadatos del
servidor revalidados: prompt_version completo, hashes disponibles y usage,
attested: false. Se prioriza el manifiesto efectivo sobre el inicial; no se
rebautiza el hash del bundle como prompt_sha256. La guía mantiene el contrato
compartido con JUP-071 y el dashboard de JUP-121.

all-repetitions valida todas las exportaciones antes de crear un directorio
nuevo. collect y export muestran resumen; strict guarda la evidencia antes de
devolver 3 por resultado parcial. Los errores propios imprimen motivos constantes
y los importados conservan la ocultación de texto arbitrario potencialmente sensible.

La autorización actual no requiere inferencias: se valida con pruebas offline
y la suite JUP-071 real contra un servidor local simulado. La integración con un
despliegue de A y los juicios independientes quedan para sus responsables.
