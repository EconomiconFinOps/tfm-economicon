JUP: JUP-138 · Trello: https://trello.com/c/WvzuP74W/130-jup-138

## Context

Motivación en `proposal.md` (Why). El estado de partida que condiciona el método:

- La rama sale de develop `03e97ce6` (22/10/2026, JUP-089). Entre el corte actual del documento (`a0e9a56`) y
  esa SHA se integraron JUP-089, 113 a 135 y 131. JUP-131 sigue con su change sin archivar y su ensayo AWS
  pendiente, así que su documentación operativa se mueve casi a diario.
- Ninguna prueba ni herramienta lee `docs/architecture.md`; la única coincidencia es un nombre de fixture en
  `tools/assistant-corpus.test.mjs`. Cambiar el texto no rompe la CI, pero tampoco hay ningún control
  automático que detecte desfases: la verificación es manual y tiene que quedar registrada.
- `docker compose config` no resuelve sin las variables obligatorias (`MINIO_ROOT_USER`, `CHAT_HMAC_FILE`, …)
  y con `--no-interpolate` lista los servicios pero falla al listar volúmenes.
- `docs/adr/README.md` enlaza anclas de `architecture.md` (§4 y §7); no hay más enlaces con ancla desde el
  repositorio.
- Hay números de ADR duplicados: 0013 (pgvector y cobertura de etiquetas), 0022 (artefactos documentales y
  evaluación en Grafana) y 0023 (chunking y un alias hacia 0025).

## Goals / Non-Goals

**Goals:**

- Que cada afirmación del documento tenga una fuente en la SHA del corte, y que la correspondencia entre
  afirmación y fuente quede en `review.md` para que la revisión pueda repetirla.
- Que la persona que revisa pueda comprobar los recuentos de servicios y volúmenes con un comando.
- Cambios por sección que conserven el estilo, los diagramas Mermaid y las anclas existentes.

**Non-Goals:**

- Reescribir el documento ni reorganizar sus secciones.
- Describir el estado del ensayo AWS, las regiones o el runner de JUP-131. Eso es de
  `docs/deployment/aws-defensa.md` y `docs/continuidad/cloud-aws.md`.
- Corregir otros documentos desfasados (`docs/assistant-corpus/product-architecture/`, README de las apps,
  `docs/architecture-aws.md`). Los que se detecten se anotan como hallazgos.
- Añadir un control automático de deriva documental. Si se considera útil, será otra tarjeta.

## Decisions

### D1. El corte es la SHA base de la rama y se recontrasta si develop se mueve

El corte es la SHA de develop sobre la que se trabaja (`03e97ce6` al empezar). Si antes del PR entra en develop
un cambio que toque Compose, rutas, migraciones o la configuración de chat, RAG o AWS, se actualiza la rama, se
revisa solo el diff entre el corte anterior y el nuevo sobre esas fuentes y se mueve el corte. La cabecera nunca
declara una SHA contra la que no se verificó.

*Alternativa descartada:* declarar como corte la SHA del merge. Todavía no existe al redactar y no se habría
verificado contra ella.

### D2. Inventario de fuentes antes de editar, guardado en review.md

Antes de tocar el documento se genera un inventario en la SHA del corte:

- Servicios, redes, secretos y volúmenes de Compose para el perfil por defecto, `demo` y el overlay `ai`.
- Rutas `@router.*` del backend, rutas del processor y migraciones por servicio.
- Flags y valores por defecto del chat y de RAG en `docker-compose.yml` y en la configuración.

Cada desfase de la lista de la tarjeta, y cada uno nuevo, se registra con tres datos: la afirmación del
documento, la fuente que la contradice o la confirma, y el cambio aplicado.

Para Compose se usa un archivo de entorno con valores ficticios en el scratchpad, nunca en el repositorio, y
`docker compose --env-file <tmp> [-f …] [--profile …] config --services | --volumes`. Los comandos exactos y
su salida van a `review.md`; los valores ficticios no.

*Alternativa descartada:* contar a mano en `docker-compose.yml`. Ya produjo una cifra que había que
confirmar, y no tiene en cuenta los perfiles ni el `include` del gateway.

### D3. Cómo describir lo integrado pero desactivado

Para el chat generativo y la recuperación contextual e híbrida, el documento dice qué está integrado, qué flag
lo activa, su valor por defecto en Compose y qué recorrido sigue la demo por defecto. La figura de §3.4 conserva
como objetivo solo lo que no está integrado (tools deterministas conectadas al agente). Las conexiones que
ahora existen pasan a flecha continua y lo condicionado por un flag se rotula. La fuente para cada elemento es
el código y la configuración, no las notas de continuidad.

### D4. AWS en versión mínima

§6.3 conserva su figura conceptual y añade un párrafo con cuatro hechos:

- el código admite los modos PostgreSQL/RDS, Cognito y Bedrock;
- existe un pipeline de creación y retirada con su ADR-0027 en estado Proposed;
- a fecha del corte no hay despliegue;
- el estado operativo se consulta en el runbook y en la nota de continuidad.

Se retira la frase «no se desplegará», que hoy es falsa. §5 añade una frase sobre el modo Cognito como
alternativa para AWS, sin alterar lo que dice de la autenticación de la demo (ADR-0014).

*Alternativa descartada:* describir regiones, runner y pipelines. Quedaría obsoleto con el primer ensayo y
duplicaría el runbook.

### D5. ADR por archivo, sin renumerar

En §7 y donde se citen, los ADR se enlazan por su nombre de archivo completo. Así los duplicados se distinguen
y no se tocan sus identificadores ni sus estados. ADR-0023 de modelo se cita a través de ADR-0025, su destino
canónico.

### D6. Estilo y anclas

Se mantienen los títulos de sección y, por tanto, las anclas que usa `docs/adr/README.md`. Si un título tiene
que cambiar, se actualizan en el mismo commit los enlaces que lo usan. Cada diagrama Mermaid editado se
comprueba en la vista previa de Markdown, y la comprobación se registra en `review.md`.

## Risks / Trade-offs

- **[develop se mueve durante el trabajo]**: JUP-131, JUP-135 y el chat siguen activos. → D1: diff acotado
  entre cortes antes del PR y nueva verificación de las secciones afectadas.
- **[Describir el chat como más o menos activo de lo que es]**: el contexto de JUP-123 a JUP-135 está repartido
  en muchas notas. → D3: la fuente es la configuración y las rutas; las dudas se anotan en `review.md` y no se
  resuelven por intuición.
- **[Documento más largo y más difícil de leer]**: hay muchas capacidades nuevas. → Una o dos frases por
  capacidad con enlace al runbook o ADR que la desarrolla; el detalle se queda en su documento.
- **[Verificación solo manual]**: sin un control automático el documento volverá a desfasarse. → Se acepta en
  esta tarjeta y se propone como hallazgo una comprobación de los servicios de Compose frente al documento.
- **[Recuentos dependientes del entorno]**: los perfiles y el overlay cambian el número de servicios. → Se dan
  los recuentos por combinación (por defecto, `demo`, `ai`) y el comando que los reproduce.

## Migration Plan

No aplica: solo documentación. Para deshacerlo basta revertir el commit.
