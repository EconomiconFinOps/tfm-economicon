# JUP-065 — Demo funcional preparada

[Tarjeta](https://trello.com/c/SZUFo4ol). Preparación: 2026-10-01. Base integrada examinada: `de0d62e7c0028f35a81c5087f531d19031a90e81` de `origin/develop`.

**Estado: preparación publicada para revisión; ensayo integrado y cierre pendientes.** No se ha desplegado, cargado una base de datos ni ejecutado un LLM en esta tarea.

## Contenido y uso

1. [Guion de siete minutos](guion.md): acciones, discurso, resultados y alternativa ante fallos.
2. [Preparación y comprobaciones](preflight.md): entorno aislado, carga, repetición y condiciones para realizar la demo.
3. [Registro de ensayo](registro-ensayo.md): completar sobre el commit realmente desplegado.
4. [Datos y referencias generados](generado/procedencia.json): commit y SHA-256 de cada fuente; copias exactas de Git y licencia Microsoft.
5. [Costes esperados](generado/costes-esperados.json), [consulta de carga](generado/consulta-costes.json), [prompts](generado/prompts.json) y [rúbricas para el evaluador](generado/rubricas-privadas.json).
6. [Procedimiento del ensayo integrado](ensayo-integrado.md): puertas de entrada JUP-035/036, secuencia y aceptación pendiente.
7. [Preparador reproducible](preparar.py), [verificación offline](verificar.py) y [evidencia de publicación](../../evidence/JUP-065-validation.md).

Desde la raíz del repositorio, Python 3.10+, Node.js 22+ y Git:

Comprobar primero el material publicado, sin ejecutar `preparar.py` sobre
`generado/`: sobrescribir los originales podría ocultar una alteración.

```powershell
python docs/demo/JUP-065/verificar.py --repo .
python -m unittest discover -s docs/demo/JUP-065 -p 'test_*.py' -v
node docs/demo/JUP-065/generado/sources/tools/validation-questions.mjs validate
```

Si se necesita una copia regenerada, crearla aparte después de esas comprobaciones:

```powershell
$demoOutput = Join-Path ([IO.Path]::GetTempPath()) ('jup065-' + [guid]::NewGuid().ToString('N'))
python docs/demo/JUP-065/preparar.py --repo . --output $demoOutput
```

El preparador lee objetos Git del commit fijo, no los archivos modificados del checkout. Para diagnosticar un objeto ausente antes de ejecutar, usar `git cat-file -e "de0d62e7c0028f35a81c5087f531d19031a90e81^{commit}"`. Si falla, recuperar ese objeto y repetir la comprobación. El objeto debe estar disponible: en un clon superficial, ejecutar primero `git fetch origin de0d62e7c0028f35a81c5087f531d19031a90e81`. CI obtiene el historial completo para el job de gobernanza. No instala dependencias, no accede a servicios y solo escribe en `generado/` o en el destino `--output`. El verificador regenera en un temporal y compara todos los bytes. No guardar resultados de ensayos dentro de `generado/`, porque se reconstruye.

## Decisiones y alcance

- Recorrido principal: muestra pública de costes → explicación conceptual con fuente → reconocimiento de límites. El valor demostrado será trazabilidad y consulta asistida, no ahorro monetario demostrado.
- La muestra pública da **0,06 USD**, a partir de 40 filas CSV y 38 registros agregados por recurso/grupo/día/moneda. Son importes pequeños reales de la muestra: no multiplicarlos para embellecer la demo. No representa una factura mensual completa.
- Para una explicación aritmética más legible existe el caso opcional **JUP-069-001: 1.000 EUR sintéticos, Virtual Machines 600 EUR / 60 %**. Se introduce su contexto íntegro en una conversación nueva; nunca se presenta como el resultado del dashboard.
- La pregunta conceptual principal es JUP-069-004, sin cifras de cliente. Usar el panel lateral «Asistente FinOps» tras aceptar A/JUP-122 y B/JUP-123 y autorizar CHAT_ENABLED=true. `/assistant` conserva consultas estructuradas Azure/propiedad/anomalía; esa pantalla no sustituye el recorrido generativo.
- En `/`, coste, desglose y serie del dashboard JUP-055 consumen registros de `/billing/summary`; la fuente de este ensayo sigue siendo la muestra Azure simulada. Elegir junio de 2024 en los dos controles mensuales según el guion, conservando la carga y referencia diarias fijadas. No incorporar otros paneles como evidencia de este recorrido: algunas rutas antiguas se han ocultado y anomalías dispone de su propio contrato; no trasladar sus resultados a esta muestra sin comprobarlos. Ahorro potencial sigue no disponible.
- Se conservan las responsabilidades de Trello: Alejandro liderazgo, Lucia pairing, Paris revisión, Victor validación. Preparar este material no acredita la participación ni aprobación de esas personas.
- La defensa completa pertenece a JUP-066; métricas y evaluación global a JUP-067/068/070/071. Cinco prompts seleccionados no sustituyen la batería de 28 ni prueban calidad global.

## Dependencias comprobadas y pendientes

Corte histórico de preparación del 01/10: snapshot `snapshot-20261001T190808Z.json` del puente autorizado DockerServer. JUP-065 estaba en Backlog, JUP-022/023 en Backlog, JUP-025 en revisión y JUP-021 pendiente de revalidación. No es un estado operativo actual. La actualización del 03/10 incorpora develop `d6fc408`, incluidas JUP-021 y JUP-050; conserva el commit original de datos sin alterar sus quince artefactos. La integración de esas tareas no acredita el ensayo completo de JUP-065.

Corte 15/10/2026: base `develop` `53b43bb1`, con A/JUP-122 (PR130) y JUP-036
(PR69) integradas. B/JUP-123 sigue sin aceptación; el chat está apagado por defecto.
JUP-119 sustituye el cargador sintético antiguo: no activar el perfil `demo` ni
`demo_data.py apply` en la instancia de esta muestra. El preflight explica
`status`/`remove`, HMAC, migraciones, subred privada y el panel nuevo.
Los quince artefactos siguen fijados a `de0d62e`; no son el corpus actual de
JUP-129 ni los datos desplazados de JUP-119. Su integridad no valida un índice nuevo.

Antes del ensayo: integrar y validar base vectorial, embeddings/retrieval, modelo real y citas visibles; comprobar que el panel lateral usa realmente ese proveedor y el índice correspondiente. Activar variables en el processor por sí solo no acredita el chat. Registrar versiones/dimensiones y reconstruir el índice si cambian. JUP-026/097/098 aportan la base de costes/datos/sesión, pero deben comprobarse otra vez en el despliegue elegido.

El cierre de JUP-065 requiere un ensayo completo registrado, reproducido por otra persona, fallos resueltos o limitaciones aceptadas, evidencias enlazadas y revisión/validación según Trello. La preparación presente satisface el trabajo adelantable pedido, sin declarar completada la tarjeta.

## Revisión de esta entrega

Esta PR cubre únicamente la preparación reproducible. Paris revisa el guion, alcance y código auxiliar; Victor reproduce las comprobaciones offline y valida la preparación. Víctor validó `f27eb7f` el 11/10 con runtime/mock y Paris lo aprobó el 13/10. La nueva combinación requiere revalidación de lo afectado, y el pairing de Lucía sigue pendiente de acreditar. No se requiere levantar el MVP para validar esta fase; su ensayo completo conserva el registro `not_run`.
