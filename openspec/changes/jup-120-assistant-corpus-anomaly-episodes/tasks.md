JUP: JUP-120

## 1. Contenido del corpus

- [ ] 1.1 Leer del código del frontend los textos exactos del panel de anomalías (títulos, botones, etiquetas de criticidad, estado y observación, aviso de datos sintéticos) y de `docs/api/anomaly-episodes.md` y ADR-0020 los hechos de D2; anotar cuáles de JUP-119 (#127) y JUP-038 (#128) están ya en `develop` para decidir qué entra en la guía.
- [ ] 1.2 Reglas de negocio: reescribir la sección `Anomalias` conservando el encabezado, la regla y la frase de límites estrictos al principio, y añadiendo después episodio, lo esperado y referencia anclada, tolerancia de 3 días, severidad por impacto acumulado con umbrales nominales en EUR y USD, estados reales (sin `acknowledged`) y servicio sin gasto previo (D2, D3).
- [ ] 1.3 Contexto de producto: guía de usuario del panel con el lenguaje de la pantalla, sin endpoints, tablas ni nombres de servicios, y diciendo que el panel no actúa sobre recursos; solo lo que está en `develop`.
- [ ] 1.4 FinOps y glosario: ajustar el flujo de trabajo de anomalías y las definiciones de `Anomaly` y `Baseline` para que no contradigan las reglas, sin repetir definiciones.
- [ ] 1.5 Manifiesto: subir la versión y `updated_at` de los documentos modificados; `assistant-corpus:validate` y `assistant-corpus:test` en verde.
- [ ] 1.6 Comprobar a mano que la regla y la frase de límites estrictos caen en el primer fragmento de la sección `Anomalias` con el troceador real (500 con solape 50) y que ningún documento nombra un endpoint, cabecera o tabla.

## 2. Cadena de huellas

- [ ] 2.1 **AVISAR a Lucia antes de empezar este grupo** para que avise a Alejandro y a Paris (JUP-035): a partir de aquí cambia la huella de la batería JUP-069 que fija su campaña (#120 y #121). No empezar hasta que Lucia confirme el momento.
- [ ] 2.2 Volver a fijar los sha256 de las fuentes modificadas en `docs/validation/JUP-069-questions.json`, subir `suite_version` y comprobar que los casos son idénticos ignorando `sources` y `suite_version`; `validation-questions:validate` y `:test` en verde.
- [ ] 2.3 Actualizar las huellas y las etiquetas de `docs/validation/JUP-022-retrieval-labels.json` y comprobar que cada encabezado etiquetado existe; `retrieval-labels:validate` y `:test` en verde.
- [ ] 2.4 Repetir `tools/retrieval-calibration.py` con el proveedor simulado para comprobar la mecánica y las pruebas `retrieval-calibration:test`. Ese resultado no se presenta como calidad de recuperación.
- [ ] 2.5 **AVISAR a Lucia antes de ejecutar** la calibración con el gateway real (necesita clave virtual y gasta crédito); si no se ejecuta, registrarla como no ejecutada. Con ella, comparar por caso las secciones recuperadas antes y después en 003, 013, 014 y 016 a 019, y recortar el texto si aparecen fragmentos de anomalías en preguntas ajenas.
- [ ] 2.6 Comprobar que ninguna prueba vuelve a validar los informes `JUP-070-run-1` y `run-2` contra la batería actual y anotar en la documentación de validación que su huella ya no coincide (D5).

## 3. Documentación y hallazgos

- [ ] 3.1 Marcar `RF-114-001` como resuelto en `openspec/findings/backlog.md` y registrar lo que queda abierto: batería de anomalías (D6), fecha de referencia y enlace «Explicar en el asistente» si no estaban integrados.
- [ ] 3.2 Nota de continuidad en `docs/continuidad/` y actualización de `docs/validation/README.md` si menciona la huella o la versión de la batería.
- [ ] 3.3 Actualizar la nota fechada de ADR-0020 que aplazaba el corpus, sin ADR nuevo.

## 4. Cierre y verificación

- [ ] 4.1 Batería completa: `corepack pnpm openspec:validate`, `jup:check -- --change jup-120-assistant-corpus-anomaly-episodes`, `jup:cleanup:check`, `assistant-corpus`, `validation-questions`, `retrieval-labels`, `retrieval-calibration:test`, `lint` y `test` del workspace, y `git diff --check`.
- [ ] 4.2 Revisión adversarial con el agente `adversarial-reviewer` hasta `accept`: contradicciones entre documentos, adjetivos de la spec («estricto», «candidata», «acumulado») aplicados a cada campo, casos 016 a 019 y 003 frente al texto nuevo, y barrido del mismo patrón (otras menciones de «EUR/mes» o `acknowledged` en el corpus y en la documentación).
- [ ] 4.3 Redactar `review.md` con lo que se comprobó, lo que no y los límites de la evidencia.
- [ ] 4.4 `## Human Approval` posterior a la revisión, por Lucia.
- [ ] 4.5 **AVISAR a Lucia antes de abrir el PR** para que avise a Alejandro y a Paris de la fecha de integración respecto a la campaña de JUP-035.
- [ ] 4.6 Archivar el change en el mismo PR y abrir el PR contra `develop`.
