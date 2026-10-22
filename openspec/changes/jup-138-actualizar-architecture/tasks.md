## 1. Inventario en la SHA del corte (D1, D2)

- [ ] 1.1 Fijar la SHA de corte (base de la rama) y crear en el scratchpad un archivo de entorno con valores
  ficticios para las variables obligatorias de Compose, sin copiarlo al repositorio
- [ ] 1.2 Listar servicios y volúmenes con `docker compose config` para el perfil por defecto, `demo` y el
  overlay `ai`, y redes y secretos del archivo combinado; registrar los comandos y su salida en `review.md`
- [ ] 1.3 Listar las rutas del backend y del processor, las migraciones y tablas de cada servicio, y los flags
  de chat, RAG y AWS con su valor por defecto; registrarlo en `review.md`
- [ ] 1.4 Contrastar cada afirmación de las secciones afectadas con el inventario y abrir en `review.md` la tabla
  de desfases (afirmación, fuente, cambio previsto), incluidos los de la tarjeta y los nuevos

## 2. Editar docs/architecture.md: componentes, flujos y datos (§1 a §4)

- [ ] 2.1 Actualizar en `docs/architecture.md` la cabecera (fecha y SHA del corte) y §1, de modo que el resumen distinga el chat
  determinista, el chat generativo integrado y lo que sigue siendo objetivo
- [ ] 2.2 §2: añadir MinIO, la landing pública y la conexión privada backend → processor en el diagrama y la
  tabla de componentes, cada uno con su límite y enlace a su fuente
- [ ] 2.3 §3.1: describir el chat generativo (generaciones, eventos, parada, reanudación y resumen) y la
  recuperación contextual e híbrida, con sus flags y valores por defecto (D3); corregir «no llama al processor»
  y la referencia a JUP-035
- [ ] 2.4 §3.2: describir la subida por URL firmada a MinIO, la extracción aislada y el chunking estructural, y
  corregir lo que se dice de `text_content`, `artifact_uri` y los endpoints de estado
- [ ] 2.5 §3.4: dejar como objetivo solo lo no integrado y pasar a flecha continua, con rótulo, lo integrado
  bajo flag (D3)
- [ ] 2.6 §4: recontar tablas y migraciones por servicio y añadir el almacén de objetos al mapa de datos

## 3. Editar docs/architecture.md: identidad, despliegue y decisiones (§5 a §8)

- [ ] 3.1 `docs/architecture.md` §5: añadir el modo Cognito como alternativa para AWS sin cambiar lo que se dice de la autenticación de
  la demo (D4)
- [ ] 3.2 §6.1: actualizar la figura de topología, los recuentos por combinación de perfiles con el comando que
  los reproduce, la tabla de versiones (MinIO) y las dependencias de arranque; recomprobar la frase de «las
  cuatro apps»
- [ ] 3.3 §6.3: añadir el párrafo mínimo de JUP-131 y retirar «no se desplegará», con enlaces al runbook, la nota
  de continuidad y ADR-0027 (D4)
- [ ] 3.4 §7: citar ADR-0022 a ADR-0027 por su archivo canónico, sin renumerar ni cambiar estados (D5)
- [ ] 3.5 §8: corregir los recuentos del CD privado si ya no son ciertos; revisar
  `docs/deployment/dockerserver-cd.md` y, si contradice el Compose actual, anotarlo como hallazgo sin editarlo

## 4. Comprobación y cierre

- [ ] 4.1 Comprobar que todos los enlaces relativos de `docs/architecture.md` resuelven a archivos existentes y que las
  anclas que usa `docs/adr/README.md` siguen existiendo (D6)
- [ ] 4.2 Ver en la vista previa de Markdown cada diagrama Mermaid editado y anotarlo en `review.md`
- [ ] 4.3 Cerrar la tabla de desfases de `review.md` (todos aplicados o justificados) y registrar los hallazgos
  fuera de alcance (corpus del asistente, README de apps, comprobación automática de deriva)
- [ ] 4.4 Si develop se ha movido, actualizar la rama, revisar el diff entre cortes sobre las fuentes de 1.2 y
  1.3 y mover el corte (D1)
- [ ] 4.5 Actualizar `docs/continuidad/README.md` y `docs/continuidad/arquitectura-tecnica.md`
- [ ] 4.6 `corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-138-actualizar-architecture`
  y `corepack pnpm jup:cleanup:check` en verde
