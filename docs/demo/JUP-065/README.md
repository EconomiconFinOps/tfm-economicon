# JUP-065 — Demo funcional preparada

[Tarjeta](https://trello.com/c/SZUFo4ol). Preparación: 2026-10-01. Base integrada examinada: `de0d62e7c0028f35a81c5087f531d19031a90e81` de `origin/develop`.

**Estado: preparación publicada para revisión; ensayo integrado y cierre pendientes.** No se ha desplegado, cargado una base de datos ni ejecutado un LLM en esta tarea.

## Contenido y uso

1. [Guion de siete minutos](guion.md): acciones, discurso, resultados y alternativa ante fallos.
2. [Preparación y comprobaciones](preflight.md): entorno aislado, carga, repetición y condiciones para realizar la demo.
3. [Registro de ensayo](registro-ensayo.md): completar sobre el commit realmente desplegado.
4. [Datos y referencias generados](generado/procedencia.json): commit y SHA-256 de cada fuente; copias exactas de Git y licencia Microsoft.
5. [Costes esperados](generado/costes-esperados.json), [consulta de carga](generado/consulta-costes.json), [prompts](generado/prompts.json) y [rúbricas para el evaluador](generado/rubricas-privadas.json).
6. [Preparador reproducible](preparar.py), [verificación offline](verificar.py) y [evidencia de publicación](../../evidence/JUP-065-validation.md).

Desde la raíz del repositorio, Python 3.10+, Node.js 22+ y Git:

```powershell
python docs/demo/JUP-065/preparar.py --repo .
python docs/demo/JUP-065/verificar.py --repo .
python -m unittest discover -s docs/demo/JUP-065 -p 'test_*.py' -v
node docs/demo/JUP-065/generado/sources/tools/validation-questions.mjs validate
```

El preparador lee objetos Git del commit fijo, no los archivos modificados del checkout. El objeto debe estar disponible: en un clon superficial, ejecutar primero `git fetch origin de0d62e7c0028f35a81c5087f531d19031a90e81`. CI obtiene el historial completo para el job de gobernanza. No instala dependencias, no accede a servicios y solo escribe en `generado/` o en el destino `--output`. El verificador regenera en un temporal y compara todos los bytes. No guardar resultados de ensayos dentro de `generado/`, porque se reconstruye.

## Decisiones y alcance

- Recorrido principal: muestra pública de costes → explicación conceptual con fuente → reconocimiento de límites. El valor demostrado será trazabilidad y consulta asistida, no ahorro monetario demostrado.
- La muestra pública da **0,06 USD**, a partir de 40 filas CSV y 38 registros agregados por recurso/grupo/día/moneda. Son importes pequeños reales de la muestra: no multiplicarlos para embellecer la demo. No representa una factura mensual completa.
- Para una explicación aritmética más legible existe el caso opcional **JUP-069-001: 1.000 EUR sintéticos, Virtual Machines 600 EUR / 60 %**. Se introduce su contexto íntegro en una conversación nueva; nunca se presenta como el resultado del dashboard.
- No se presupone que el chat consulte automáticamente la tabla de costes: el backend de chat y el pipeline estructurado siguen separados. La pregunta conceptual principal es JUP-069-004, sin cifras de cliente.
- Mostrar únicamente la sección conectada de `/`; evolución, inventario, exportación, anomalías y recomendaciones conservan componentes demo. Ahorro potencial sigue no disponible.
- Se conservan las responsabilidades de Trello: Alejandro liderazgo, Lucia pairing, Paris revisión, Victor validación. Preparar este material no acredita la participación ni aprobación de esas personas.
- La defensa completa pertenece a JUP-066; métricas y evaluación global a JUP-067/068/070/071. Cinco prompts seleccionados no sustituyen la batería de 28 ni prueban calidad global.

## Dependencias comprobadas y pendientes

Consulta del tablero mediante el puente autorizado DockerServer: snapshot `snapshot-20261001T190808Z.json`. JUP-065 seguía en Backlog; no se cierra. JUP-022 (retrieval real) y JUP-023 (gateway/modelos) siguen en Backlog; JUP-025 (citas) en revisión. La continuidad de JUP-021 registra PR #53 pendiente de revalidación; no se incorpora su rama al paquete. Estos estados no prueban ausencia total de código, pero impiden afirmar aceptación del recorrido integrado.

Antes del ensayo: integrar y validar base vectorial, embeddings/retrieval, modelo real y citas visibles; comprobar que la ruta `/assistant` usa realmente ese proveedor y el índice correspondiente. Activar variables en el processor por sí solo no acredita el chat. Registrar versiones/dimensiones y reconstruir el índice si cambian. JUP-026/097/098 aportan la base de costes/datos/sesión, pero deben comprobarse otra vez en el despliegue elegido.

El cierre de JUP-065 requiere un ensayo completo registrado, reproducido por otra persona, fallos resueltos o limitaciones aceptadas, evidencias enlazadas y revisión/validación según Trello. La preparación presente satisface el trabajo adelantable pedido, sin declarar completada la tarjeta.

## Revisión de esta entrega

Esta PR cubre únicamente la preparación reproducible. Paris revisa el guion, alcance y código auxiliar; Victor reproduce las comprobaciones offline y valida la preparación. La revisión, validación humana y pairing siguen pendientes hasta disponer de evidencia explícita. No se requiere levantar el MVP para validar esta fase; su ensayo completo conserva el registro `not_run`.
