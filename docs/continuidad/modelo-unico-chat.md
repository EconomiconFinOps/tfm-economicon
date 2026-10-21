# Modelo único del chat — JUP-132

[Tarjeta](https://trello.com/c/ERLZlPsT) ·
[Change archivado](../../openspec/changes/archive/2026-10-21-jup-132-default-chat-model/) ·
[ADR-0026](../adr/ADR-0026-default-chat-model.md).

Base b7c8b708 del21/10/2026; rama feat/JUP-132-default-chat-model.
Paris lidera; Alejandro pairing; Lucía revisión; Víctor validación.
La asignación no acredita participación o aprobación humana.

## Resultado preparado

economicon-chat resuelve únicamente a openrouter/deepseek/deepseek-v4.1-flash
por DeepInfra FP8 normal. Se retira la alternativa Pro. Chat, compresión y
diagnóstico usan esa ruta, reasoning desactivado y ningún fallback; privacidad,
límites, permisos y concurrencia se mantienen. El diagnóstico exige un certificado
operativo nuevo y válido para la ruta: no se reutiliza una autorización GLM.

Recursos activos chat/summary v4 con tokenizer Flash oficial fijado, preparado
fuera de Git. v2/v3, sus huellas y tokenizer anteriores se conservan como lectores;
no se reescriben resúmenes ni se permite generar con lectores históricos.
Embeddings, dimensión1536, corpus e índices no cambian.

## Comprobaciones y límites

Se conservan las reproducciones negativas y fallos de preparación. Configuración,
contratos nuevos/antiguos y regresiones focales se comprueban offline; Docker
empaqueta los recursos para uso sin descarga durante ejecución.
Los smokes aislados usan únicamente upstream/credenciales sintéticos.
La evidencia identifica el candidato local R2 congelado y sus límites.

[Resultados propios y límites](../evidence/JUP-132-validation.md): tres smokes
Docker resueltos, builds offline y contratos históricos/nuevos comprobados.
Las omisiones de calidad/proveedor real y memoria canónica son explícitas.

No hay prueba contra OpenRouter real, medición de calidad o gasto. Las campañas
anteriores y ADR-0025 mantienen su fecha/modelo/coste; no validan este cambio.
No se despliega ni cambia el gateway compartido, no se emiten claves reales,
no se modifica memoria canónica ni se declara consenso del equipo.
La revisión independiente R2 es favorable: los dos hallazgos R1 se corrigieron;
se ejecutaron 60 comprobaciones propias y se reutilizó una del liderazgo de forma
explícita. La validación independiente R2 es favorable exclusivamente offline:
11 comprobaciones propias adicionales y evidencia R1 reutilizada por identidad.
PM verificó el retorno contra las mismas referencias originales, sin cambios.

Paris autorizó el archivado, commit y push el 21/10/2026. OpenSpec quedó archivado
como `2026-10-21-jup-132-default-chat-model`, con requisitos promovidos y enlaces
actualizados. La ratificación, el pairing y las reviews humanas siguen pendientes;
la publicación de la PR requiere aprobación del mensaje. Este cierre local no
acredita despliegue ni cierre de la tarjeta.
