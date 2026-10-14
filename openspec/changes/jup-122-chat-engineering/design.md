# Diseño JUP-122

Base: develop c30a7d0. Se integra el árbol base de Paris f63c150 mediante
reconciliación de tres vías, conservando anomalías reales, navegación española,
demo JUP-119 y fecha de referencia. La reconciliación de migraciones 002/005
procede de 731b5ea; no elimina tablas ni histories existentes.

De PR121 se extraen exclusivamente los bloques de ingeniería. Se mantiene el
protocolo original required-documentation-v1: ni auto-decision ni expresiones,
segmentos, clasificación o draft/final de B. El arreglo histórico de 551fb81
se adapta al finish=length de la búsqueda nativa requerida, con prueba exacta
502/incomplete y reintento backend sin persistir una pareja parcial.

Las pruebas de operaciones conservan ese protocolo original. Las correcciones
de frontend son reconciliación con develop y gestión del foco; no generación.
El transporte summary incorpora 97e8e043, independiente del contrato de respuesta.

CHAT_ENABLED=false es el valor por defecto de Compose. El arranque no crea el
planificador; generate/resume/summary-retry rechazan iniciar trabajo con 503.
El historial y las acciones de parada siguen accesibles. La UI conserva los
estados de error existentes; esta entrega no promete un asistente activo.

El archivo OpenSpec de JUP-035 se conserva como antecedente, no como prueba de
cierre actual. JUP-035 sólo puede cerrarse tras A y B. A requiere sus propias
Revision JUP-122 y Validacion JUP-122; no se heredan aprobaciones de otras PR.

Las evidencias SQL y UI no ejecutadas permanecen pendientes. CI técnica y
pruebas sintéticas no acreditan la calidad de las respuestas reales.

## Adaptacion acotada de tres mejoras
Destino: `codex/JUP-122-checkpoint-improvements`, base vigente de PR130
`318a56f31828be50f8960860f69172f51046734d`. Referencias solo de lectura:
checkpoint de Paris `98586e860d5c625441f9fd69ab3377a8638baf7e` y tokenizer
`a8f4dddc05d85b17ed2023388c8857d1ce538882`.

Este alcance sustituye el borrador anterior de siete puntos. No se incorporan
preparacion local HMAC, recuperacion UI del resumen, rechazo de memoria vacia,
reinicio/liberacion de buffers ni soluciones semanticas de JUP-123/B.

1. Tokenizer fuera de Git: adaptar `apps/processor/build_tokenizer.py` y su test.
   Descarga solo en build o preparacion explicita desde `zai-org/GLM-5.2`,
   revision `a66456a59f21345d1e5e586345c448a9106d29d7`, 20217442 bytes y SHA256
   `19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`.
   Cache verificada sin red, reemplazo atomico solo tras integridad y rechazo
   de corrupcion. Docker backend/processor genera el mismo recurso en la ruta
   vigente; CI prepara antes de las suites que lo necesitan. Git y ambos
   contextos Docker lo excluyen. Se documenta `tokenizer:prepare`; los
   manifiestos conservan sus pins porque el artefacto efectivo no cambia.
2. CD excluye `.secrets` en raiz y subdirectorios mediante el filtro de copia
   existente. Git y contextos Docker tambien lo excluyen. Se conserva
   exactamente la provision HMAC actual, permisos y rechazo de symlinks.
   Pruebas con secretos sinteticos acreditan exclusion y no rotacion.
3. Fixture SQL del processor: adaptar datos sinteticos propios en la base
   configurable y esperar `wait_for(shield(job.task))` antes de afirmar settled.
   Conservar las aserciones de cierre fisico, query cancelada y conexion
   principal, y el escenario de cierre retenido que demuestra la carrera.
   La fixture portable del backend se conserva. CI SQL incluye la suite
   afectada del processor en un entorno con sus dependencias y DB propios.

### Comprobaciones y limites
Red/Green focales: descarga positiva/corrupta/cache offline, exclusion nested
de secretos, HMAC/symlinks existentes y limpieza SQL real sin omisiones.
Build de ambas imagenes y carga de recursos offline con hashes coincidentes.
Regresiones afectadas de recursos, topologia, CI y runtime off; controles
obligatorios de gobernanza, OpenSpec, trazabilidad e higiene del proyecto.

No cambio de prompts, schemas, protocolos, generacion, evaluacion, presupuestos
ni deadlines del producto. `CHAT_ENABLED=false` y el comportamiento de A
permanecen vigentes. Sin baterias LLM/full28 ni aceptacion semantica. Si una
dependencia o fallo exige ampliar el alcance se comunica antes de corregirlo.
Revision/validacion humanas y publicacion siguen siendo pasos separados.
