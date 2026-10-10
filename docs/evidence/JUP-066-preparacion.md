# JUP-066 — Evidencia de preparación documental

Fecha de contraste: 10/10/2026. [Tarjeta](https://trello.com/c/6HjNIvoy). Base `c2995a118d419dfe725247bac9c6f219a3f0ea77`. Entrega: [guion](../presentation/JUP-066/guion.md), [ficha de ensayo](../presentation/JUP-066/ensayo.md) y [fuentes](../presentation/JUP-066/fuentes.md).

Estado: contenido preparado para liderazgo; ensayo y dictámenes humanos pendientes. Este documento registra comprobaciones de preparación, no una review `Validacion JUP-066` ni aceptación de la tarjeta.

## Criterios de la tarjeta

| Criterio literal | Evidencia disponible | Estado y límite |
| --- | --- | --- |
| Resultado funcional verificable. | Guion oral completo, seis bloques, cuatro participantes, demo de siete minutos, incidencias, preguntas y recorte; PDF/Drive contrastados. | Preparación documental comprobable. Ensayo oral y demo integrada no ejecutados. |
| Pruebas necesarias añadidas y en verde. | Controles documentales de tiempo, cobertura, enlaces y fuentes; comandos abajo. | Sin código de producto cambiado ni tests artificiales que dupliquen el texto. Controles de ensayo definidos, aún `not_run`. |
| Documentación y decisiones actualizadas. | Guion, fuentes, ensayo, OpenSpec y continuidad. | Completado para esta contribución; no modifica los apartados ajenos de memoria. |
| Pull request revisado y vinculado. | Contribución aislada con parche para el liderazgo. | Pendiente de adopción/publicación por liderazgo y review independiente de Víctor. No hay PR de implementación JUP-066 acreditada al corte. |
| Validación funcional y evidencia enlazadas. | Esta matriz y ficha con campos de evidencia reproducible. | Validación documental propia limitada; validación independiente, cronometraje, participación y ensayo funcional pendientes. |

## Comprobaciones

- PDF oficial: extracción de texto y visualización de página física 4; SHA-256 registrado en fuentes. Duración, participación y preguntas contrastadas con la transcripción `Guion_PJ.md` de Drive. Preguntas sin duración definida.
- Memoria: lectura del documento canónico y su revisión, sin edición; reservas c–i y divergencia de viabilidad recogidas en fuentes. No se usa el borrador local como versión vigente.
- Demo: lectura de guion/preflight/README/registro en PR63 `48ee742`; el cronograma usa la UI mensual y separa el periodo fijo de carga. Se mantienen Growth limpio, fuentes pertinentes, conversación nueva y fallo explícito.
- Resultado histórico: 0/20 answer de JUP-070 y 28 fail de la batería con mock. Contrastado con informe y JSON; no ejecución nueva ni métrica generativa.
- Tiempos: 2 + 2 + 7 + 3 + 2 + 2 = 18 min; recorte 1,5 + 1,5 + 7 + 2 + 1,5 + 1,5 = 15 min. Ambos conservan las cuatro intervenciones; no acreditan tiempo oral real.

Resultados locales de preparación:

| Comando / control | Resultado | Alcance |
| --- | --- | --- |
| `node --test tools/jup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 89 pass, 0 fail, 0 skip | Herramientas de gobernanza existentes; no ejecución de la aplicación |
| `node tools/jup-check.mjs --all` | Nueve changes trazables, incluido JUP-066 | El primer intento detectó ausencia de `design.md` y `.openspec.yaml`; añadidos y repetido correctamente |
| `openspec validate --all --strict --no-interactive` | 56 pass, 0 fail | Contratos del repositorio y nuevo change de preparación |
| `verify-preparation.py <copia> <informe>` | Diez controles correctos, 25 enlaces locales resueltos | Control auxiliar fuera de Git: aritmética/continuidad de tiempos, cuatro ponentes, seis bloques, plantilla pendiente, identidad PDF, baseline mock y calendario |
| Lectura cruzada delegada del guion | Dos precisiones incorporadas y relectura conforme | Generación ausente en la base y juicio humano provisional de JUP-070; no review humana formal |

Entorno: Node **24.14.1**, Python **3.14.4**, pnpm **9.0.0**, OpenSpec **1.8.0**, YAML **2.9.0**. OpenSpec se ejecutó desde la instalación existente del workspace, con directorio de trabajo en la copia aislada. YAML se copió desde la dependencia local de igual versión a `node_modules/` ignorado de esta copia, sin modificar el lockfile ni el checkout compartido.

Incidencias de entorno resueltas: el runner Node no pudo crear procesos en el sandbox (`EPERM`); repetido con permisos de ejecución. La primera repetición encontró YAML ausente en el clon nuevo (77 pass y un archivo de tests sin cargar); tras preparar esa dependencia local, el comando completo dio 89/89. No se presenta ninguno de los intentos fallidos como verde.

Logs, controlador auxiliar, informe JSON y paquete de traspaso se conservan fuera del clon, en el workspace `materiales/07-evidencias/JUP-066-guion-2026-10-10/`. Los controles comprueban preparación documental; no se añaden pruebas que reflejen mecánicamente el texto al CI ni se ejecutan build/suites de producto sin cambios de código. La validación real de tiempos, claridad, contribuciones y demo conserva `not_run`.

## Pendientes concretos

1. Lucía adopta/revisa el discurso y acuerda con los cuatro el reparto. Paris registra su pairing real si ocurre.
2. Cada participante contrasta y confirma una aportación atribuible con enlace; no basta su asignación en Trello.
3. Liderazgo de JUP-065 aporta ensayo integrado del despliegue elegido, o mantiene el modo offline explícito. No presentar esta preparación como MVP probado.
4. Responsables de memoria/evaluación reconcilian sus apartados y la afirmación de extremo a extremo con recibos de ejecución; sustituir cifras solo con evidencia aceptada.
5. Confirmar fecha institucional y cómputo de preguntas; reconciliar 27/28 de octubre para ensayo. Ejecutar y registrar ensayo completo y recorte.
6. Publicar la entrega por el liderazgo contra develop, obtener `Revision JUP-066` y `Validacion JUP-066` según CONTRIBUTING, y enlazar evidencia en Trello. No cerrar antes.
