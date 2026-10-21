JUP: JUP-133
Trello: https://trello.com/c/Yv1ETc2G

## 1. Inventario y clasificación (sin modelo nuevo)

- [ ] 1.1 Listar las fuentes de medida reales leyendo el manifiesto, `docs/validation/` y los temas de continuidad de JUP-035/123, 070/071, 022/067, 078, 130, 068 y 063
- [ ] 1.2 Crear `docs/validation/model-dependence-inventory.json` con clase (`dependiente`, `independiente`, `historica`), justificación y comprobación por entrada
- [ ] 1.3 Comprobar en el código que el detector de anomalías y la frescura de los datos no usan el modelo de generación y registrar la comprobación
- [ ] 1.4 Validador del inventario y pruebas: una clase por entrada, justificación no vacía, fuente del manifiesto sin clasificar falla, `independiente` sin comprobación falla
- [ ] 1.5 Documento `docs/validation/model-dependence-inventory.md` con la lectura humana del inventario

## 2. Identidad del modelo en las ejecuciones (sin modelo nuevo)

- [ ] 2.1 Escribir primero las pruebas en rojo: mismo alias y distinto `generation_model_id` no comparten clave; registrada frente a no registrada tampoco; sin identidad conserva la clave actual
- [ ] 2.2 Añadir los cuatro campos a `RUN_KEYS`, a la validación (`generation_quantization` ≤ 80 caracteres, `gateway_config_sha256` sha256 de 64 minúsculas) y a `rows-v1`
- [ ] 2.3 Extender `comparability_key` para añadir la identidad solo cuando alguno de los campos no es nulo
- [ ] 2.4 Añadir las columnas al DDL de `evaluation.runs`, a la carga y a la proyección de marcas de cambio (nombrar identificador de modelo, proveedor, cuantización y configuración)
- [ ] 2.5 Soportar `model_identity` en las entradas del manifiesto: rellena solo lo que falta, rechaza claves desconocidas y conflictos con el informe, sin tocar `report_sha256`
- [ ] 2.6 Anotar en `docs/validation/evaluation-runs.json` las ejecuciones GLM-5.2 con lo que acredita la evidencia, y `null` en lo no acreditable
- [ ] 2.7 Mostrar modelo, proveedor y cuantización junto al alias en las tablas por ejecución del dashboard (`assistant-evaluation.json`) y actualizar sus pruebas de consultas y etiquetas
- [ ] 2.8 Prueba de que una ejecución posterior al cambio de JUP-132 sin identidad no entra en el manifiesto versionado
- [ ] 2.9 Actualizar `docs/validation/evaluation-dashboard.md` (contrato `run`, manifiesto, lectura de series) y añadir una nota de enmienda a ADR-0022
- [ ] 2.10 Comando de solo lectura que calcula `gateway_config_sha256` de la entrada del chat, con pruebas

## 3. Plan, plantillas y cifras de la memoria (sin modelo nuevo)

- [ ] 3.1 Escribir `docs/validation/model-reevaluation-plan.md`: por campaña dependiente, llamadas, coste estimado, proveedor, presupuesto máximo (vacío hasta que lo fije Lucia) y autorización
- [ ] 3.2 Escribir la plantilla del informe antes/después con la columna «después» vacía, las reglas de lectura (intervalos solapados, condiciones distintas, no medido) y el apartado de gasto
- [ ] 3.3 Escribir la lista de cifras de la memoria afectadas, por referencia a las secciones de `docs/memoria/README.md`, con valor anterior y valor nuevo «no medido»
- [ ] 3.4 Prueba que comprueba que cada cifra enlaza con una entrada del inventario o consta «sin origen verificable»

## 4. Reejecución y informe (bloqueado por JUP-132 y por autorización de presupuesto)

- [ ] 4.1 Confirmar que JUP-132 está integrado, o que existe un gateway aislado con `economicon-chat` apuntando a DeepSeek V4.1 Flash
- [ ] 4.2 Obtener de Lucia el presupuesto máximo por campaña y la autorización expresa de gasto en OpenRouter; registrarlos en el plan
- [ ] 4.3 Reejecutar las campañas `dependiente` dentro del presupuesto, con identidad completa del modelo en cada ejecución
- [ ] 4.4 Cargar las ejecuciones nuevas en el manifiesto y comprobar en el dashboard que forman series separadas de las de GLM-5.2
- [ ] 4.5 Rellenar el informe antes/después, la lista de cifras de la memoria, lo no reevaluado y el gasto real frente al presupuesto
- [ ] 4.6 Dejar constancia escrita de cada campaña dependiente que no se reejecutó y su motivo

## 5. Cierre y verificación

- [ ] 5.1 Pasar la batería completa: `corepack pnpm evaluation-dashboard:test`, `corepack pnpm test`, `corepack pnpm lint`, `corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-133-reevaluacion-metricas-modelo` y `corepack pnpm jup:cleanup:check`
- [ ] 5.2 Revisión adversarial con el agente `adversarial-reviewer` hasta `accept` (adjetivos de la spec en cada campo, combinaciones de identidad parcial, claves antiguas intactas)
- [ ] 5.3 Escribir `review.md` y la evidencia en `docs/evidence/JUP-133-validation.md`
- [ ] 5.4 Actualizar `docs/continuidad/README.md` y el tema `docs/continuidad/` correspondiente
- [ ] 5.5 Sección `## Human Approval` posterior a la revisión, a cargo de Lucia
- [ ] 5.6 Archivar el change en el mismo PR y abrir el PR contra `develop`
