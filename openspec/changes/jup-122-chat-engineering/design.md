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
