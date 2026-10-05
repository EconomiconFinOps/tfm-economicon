## Context

JUP-052 entrega un entorno privado desechable. DockerServer tiene Python 3.12,
Docker 29.6.2 y Compose 5.3.1; SSH accesible por LAN. El repositorio es público.
Roles Trello al comenzar: Victor líder, Alejandro pairing, Lucia revisión,
Paris validación. No se presume participación humana ni aprobación técnica.

## Decisions

ADR: [ADR-0018](../../../../docs/adr/ADR-0018-private-dockerserver-cd.md), Proposed.
CD llama al workflow CI del mismo SHA mediante workflow_call. El agente acepta
solo el último run exitoso de cd.yml en develop, del repositorio canónico y con
SHA igual al head actual; verifica otra vez el head tras el fetch/preparación.
El agente instalado permanece fijado a una revisión revisada.

Se renderiza Compose sin imprimir secretos, se fuerzan todos los puertos a
loopback, se preservan los dólares escapados por el renderer Compose y se fijan
rutas absolutas a la release. Slot alternante y proyecto por SHA separan datos
de validación. El candidato pasa build, up --wait y cinco escenarios del smoke
antes de cambiar state.json. Fallo detiene candidato y conserva la versión
actual. Rollback prueba la anterior con --no-build y pausa el agente.

## Risks / Trade-offs

No cero downtime ni endpoint estable; túneles por slot. No rollback de datos.
El agente tiene permisos Docker: solo código integrado de confianza. Sin
credenciales GitHub, depende del acceso público y sus límites; errores fallan
cerrado. Releases/volúmenes consumen disco y requieren limpieza explícita.

## Migration Plan

Ensayo aislado desde esta rama; publicar PR para los roles asignados. Integrar
tras revisión y validación. Instalar agente/unidades y verificar lingering.
Primera ejecución CD real solo después de integración en develop. Conservar
evidencia del run id y del state.json; no declarar Hecho antes de ese contraste.

## Correcciones de revisión — 2026-10-05

Revisión Lucia en PR #73 sobre 096be34: reconciliar todas las releases
inactivas de este root bajo lock, incluida previous (se conservan volúmenes),
antes de reutilizar slot y en polls sin nuevo SHA. Copias .preparing se descartan
bajo ese mismo lock. Fallos de recuperación se registran sin bloquear consulta
de elegibilidad; un fallo de limpieza sí impide reutilizar el slot.

Failure se registra antes de down con tipos de error saneados; se conserva
la excepción original aunque también falle down. Un SHA fallido queda pausado
hasta resume/nuevo SHA. Resume conserva evidencia y marca retry_allowed.
Se comprueba develop tras build/smoke antes de promover. Proyectos nuevos
incluyen hash del root, no solo SHA. Validate-source rechaza releases existentes
y pausa manual, y se documenta su promoción explícita del root de ensayo.
ADR renumerado a 0018 tras comprobar develop y diffs de PR abiertas.
El código instalado del timer no se actualiza con estas correcciones antes de
la revisión/validación: pruebas Linux en copia temporal sin Docker real.

## Segunda vuelta — 2026-10-05

Cleanup recorre todas las releases/copies, agrega errores saneados y bloquea
reutilización de slot si alguno persiste. Recovery describe el último intento
y se elimina tras resolver tanto limpieza como current, o reemplazo sano.
Tras smoke, errores de API y head superado conservan current y evidence previa,
intentan detener candidato y no lo ponen en cuarentena permanente. Events guarda
histórico privado por intento con reason; failure.json conserva último fallo
funcional y resolved_at tras reintento exitoso. Retención de releases/events
manual; directorios retirados solo después de detener/verificar proyecto propio
y bajo lock, fuera del scanner. Se mantiene resume explícito con riesgo
documentado tras rollback y config de slot inmutable (sin migración automática).

## Tercera vuelta — 2026-10-05

Evidencia best effort nunca impide cleanup ni cambia causa propagada; state
es obligatorio. Promoción resuelve failure antes de cleanup; estado pendiente
se registra con detalle saneado y aviso de current ya cambiado. Poll reintenta
resolved_at incluso sin GitHub; Already deployed conserva cleanup pendiente.
Rollback repetido con pausa verifica current sin intercambiar punteros otra vez.
Si falla reverificación, no detiene current. API persistente conserva timer5min
sin backoff automático, con pausa operativa y retención manual explícitas.
