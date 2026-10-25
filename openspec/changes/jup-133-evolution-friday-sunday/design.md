# Diseño JUP-133

Dos representaciones derivadas con fuente JUP-133 evitan duplicar denominadores
de los informes JUP-070/071. El caso y la repetición se conservan en observaciones
públicas; las cifras se regeneran, no se rellenan manualmente. Modelo declarado,
metadatos desconocidos nulos y protocolos distintos mantienen claves de
comparabilidad distintas. No se altera el contrato estricto de series existente.

El bloque adicional en sección2 tiene fechas fijas y aviso de independencia de los
selectores. Compara terminación/reintentos y tiempos observados por banco, con
denominadores diferentes; los veredictos funcionales se muestran sólo para eldomingo.
El coste se registra con nombres de métrica distintos según su base.

El SQL suplementario bloquea runs/results, compara multiconjuntos completos para
identidades existentes e inserta sólo las ausentes en una transacción. Sin DDL
permanente, borrados, roles o credenciales. La carga genérica no se modifica.
Pruebas reales usan exclusivamente PostgreSQL desechable y comprueban preservación,
colisiones, repetición y consultas vacías/parciales. Los artefactos crudos se quedan
fuera de Git; se publica una lista blanca de medidas y hashes de fuentes.
