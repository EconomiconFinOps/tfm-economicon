# Diseño JUP-126

Trello: https://trello.com/c/SplMvNMA

Separar dos preguntas: qué título aporta un rol y si existen cambios pendientes.
Mantener `published` completo, ordenado por submitted_at y excluyendo autor y
borradores. Por tipo Revision/Validacion, un Map por login normalizado conserva
el último título de la tarjeta. DISMISSED se filtra después del Map: filtrarlo
antes resucitaría el título anterior. Las dos colecciones resultantes controlan
presencia/solapamiento. La evaluación de latestDecision no cambia.

Alternativas rechazadas: editar dictámenes; excepción ficticia; aceptar cualquier
pareja distinta pese a solapamiento vigente; filtrar DISMISSED globalmente (podría
revivir Request changes); seleccionar sólo SHA actual (cambio de proceso diferente).
Se mantiene orden estable del API para marcas de tiempo iguales como en la base.
No inferir identidad de personas asignadas a partir de nombres libres.

Compatibilidad: el antiguo caso que aceptaba un único título descartado ahora
falla por rol ausente. Request changes descartado no bloquea como solicitud,
pero su título tampoco aporta rol. Una nueva review titulada puede restituirlo.
El check no interpreta texto favorable ni acredita vigencia semántica o pairing.

Decisión de proceso acotada a CONTRIBUTING/OpenSpec; no cambia arquitectura de
runtime ni introduce una nueva decisión de infraestructura que precise ADR.
Archivo técnico en esta rama no equivale a aprobación o integración del proceso.
