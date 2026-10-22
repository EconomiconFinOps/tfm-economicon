JUP: JUP-138
Trello: https://trello.com/c/WvzuP74W/130-jup-138

# Poner docs/architecture.md al día con el stack integrado

## Why

`docs/architecture.md` declara un corte de código del 11/10/2026 (develop `a0e9a56`). Desde entonces se
integraron en develop el chat generativo (JUP-122, JUP-123, JUP-132, JUP-135), la ingesta de archivos con
MinIO (JUP-124), el chunking estructural (JUP-125), la recuperación contextual e híbrida (JUP-127), los
modos de aplicación y el pipeline para AWS (JUP-131) y la landing pública (JUP-089). El documento no los
recoge y hoy afirma cosas que el código desmiente: «9 servicios base y 5 volúmenes», que el backend «no
llama al processor», que `artifact_uri` «no prueba descarga ni extracción de archivos» o que AWS «no se
desplegará». Es la referencia técnica que leen el equipo y el tribunal, y la defensa es el 29/10/2026.

## What Changes

- Fijar un corte nuevo en la cabecera con la SHA de develop contra la que se verifica cada afirmación.
- §2 Componentes: añadir MinIO (artefactos documentales temporales), la landing pública estática
  (independiente de la aplicación, fuera de Compose y con la publicación pendiente) y la conexión privada
  backend → processor del chat.
- §3 Flujos: subida de archivos por URL firmada y extracción aislada; chunking estructural; recuperación
  contextual e híbrida tras sus flags; chat con generaciones y resumen, indicando qué está activo por defecto
  (`CHAT_ENABLED=false`) y qué sigue siendo objetivo (tools deterministas conectadas al agente).
- §4 Datos: recontar las tablas y migraciones de cada servicio y añadir el almacén de objetos.
- §5 Identidad: mencionar el modo Cognito que añade JUP-131 como alternativa para AWS, sin cambiar lo que se
  dice de la autenticación de la demo.
- §6.1 Topología local: servicios, redes, secreto, volúmenes, perfiles y dependencias de arranque reales;
  recuentos que coincidan con `docker compose config`.
- §6.3 AWS, versión mínima: el código ya admite PostgreSQL/RDS, Cognito y Bedrock y existe un pipeline de
  creación y retirada; a fecha del corte no hay despliegue. Se enlaza a `docs/deployment/aws-defensa.md`,
  `docs/continuidad/cloud-aws.md` y ADR-0027, sin describir el estado del ensayo, que cambia a diario.
- §7 Decisiones: citar ADR-0022 a ADR-0027 por su archivo canónico (hay números duplicados) y el modelo
  generativo por defecto.
- §8: corregir los recuentos de servicios que cita sobre el CD privado si dejan de ser ciertos.
- Mantener sin cambios lo que sigue vigente: anomalías y billing (§3.3), datos de demostración (ADR-0021),
  secretos (§5) y observabilidad (§8).
- No cambia código, pruebas, migraciones, ADR (ni sus estados) ni specs de comportamiento.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `technical-architecture-deliverable`: se añade un requisito para que la vista de arquitectura coincida con
  el stack integrado en la SHA de su corte. Cada servicio de Compose aparece o se justifica, las capacidades
  integradas pero desactivadas por defecto se describen como tales, y la cabecera declara la SHA verificada.

## Impact

- Documentación: `docs/architecture.md` y, si alguna ancla cambia, las filas que la enlazan en
  `docs/adr/README.md` y `docs/continuidad/`.
- Continuidad: `docs/continuidad/README.md` y `docs/continuidad/arquitectura-tecnica.md` al cerrar.
- Fuera de alcance, con motivo:
  - `docs/architecture-aws.md`, Terraform y el runbook AWS: los mantiene JUP-131 y cambian con el ensayo.
  - README de las apps: cada uno tiene su propio dueño.
  - `docs/deployment/dockerserver-cd.md`: solo se revisa y, si contradice el Compose actual, se anota como
    hallazgo.
  - La memoria del TFM: es un documento compartido fuera de Git.
  - Los estados de los ADR.
- Sin cambios de runtime, datos, dependencias ni CI. Sin `docs/evidence/JUP-138-validation.md`: al ser solo
  documentación basta `review.md` (precedente JUP-083).
- ADR: no aplica. Es una consolidación documental de decisiones ya registradas.

## Human Approval

- Change: jup-138-actualizar-architecture
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-10-22
- Carril: standard
- Scope reviewed: proposal, design, specs, tasks
- Decisions approved: el corte es la SHA base de la rama, con nueva verificación del diff entre cortes si develop
  se mueve antes del PR (D1); inventario de fuentes en `review.md` antes de editar, con Compose resuelto mediante
  un archivo de entorno ficticio fuera del repositorio (D2); lo integrado pero desactivado se describe con su flag
  y su valor por defecto (D3); JUP-131 en versión mínima en §5 y §6.3, sin el estado del ensayo (D4); la landing
  pública entra en §2; ADR citados por archivo, sin renumerar ni cambiar estados (D5); se conservan las anclas
  que usa `docs/adr/README.md` (D6).
- Pendiente fuera de este gate: edición de `docs/architecture.md` (grupos 2 y 3 de tasks), review, gate
  post-review, archivo, PR y las reviews `Revision JUP-138` y `Validacion JUP-138`.
