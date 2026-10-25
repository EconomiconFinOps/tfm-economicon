# Evidencia técnica — JUP-069

Fecha: 2026-09-17. Base de implementación: `cfc6668` de `origin/develop`.
Rama: `feat/JUP-069-validation-questions`.
[Trello](https://trello.com/c/Qi5uwxgW).

## Entregable

- [Batería 1.0.0](../validation/JUP-069-questions.json): 28 casos en español,
  siete categorías, contextos sintéticos y referencias al corpus por SHA-256.
- [Protocolo](../validation/README.md): preparación de inputs sin respuestas,
  conversaciones independientes y registro de resultados para JUP-070/JUP-071.
- Herramienta offline y pruebas integradas en el job de gobernanza de CI.

## Comprobaciones locales

Entorno: Windows, Node.js 24.14.1, pnpm 9.0.0. La CI usa Node.js 22.

| Comando | Resultado |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` | Correcto, sin cambios del lockfile |
| `node tools/validation-questions.mjs validate` | 28 casos, siete categorías, fuentes y rúbricas válidas |
| `node --test tools/validation-questions.test.mjs` | 8 pruebas correctas |
| `node --test tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 13 pruebas correctas |
| `node tools/jup-check.mjs --change jup-069-validation-questions` | Trazabilidad correcta |
| `node tools/jup-cleanup-check.mjs` | Correcto |
| `corepack pnpm openspec:validate` | 31 elementos correctos, ninguno fallido |
| `git diff --check` | Sin errores de espacios |

Las pruebas negativas cubren IDs repetidos, contexto ausente, referencias
desconocidas, rúbricas vacías, pérdida de cobertura, deriva del corpus, fuentes
ausentes, rutas fuera del repositorio, estructuras inválidas y tolerancias
numéricas incorrectas. También comprueban aritmética de referencia, estabilidad
de inputs, ausencia de claves de respuesta y uso de la CLI desde otro directorio.

## Qué queda pendiente

No se ha ejecutado una evaluación de respuestas del asistente, ni se acredita
acceso a costes reales. La validación anterior prueba el instrumento, no una tasa
de acierto del producto. Revisión humana del PR y ejecución funcional mediante
JUP-070/JUP-071 pendientes; no se atribuye participación ya realizada a los roles
que Trello tiene asignados.
