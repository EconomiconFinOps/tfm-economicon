# Diseño JUP-058

## Context

Base `origin/develop` c2995a118d419dfe725247bac9c6f219a3f0ea77. El panel
existente consume directamente fixtures, sin filtros. Se siguen los patrones
de AnomaliesPanel y la capa HTTP/auth/tenant existente, sin modificar el tema.

## Goals / Non-Goals

Clasificar por tipo y dificultad, ordenar, comprender ahorro y evidencia,
y exportar lo visible. No generar recomendaciones, inventar objetivos de
coste, ejecutar mejoras ni acreditar ahorro real.

## Decisions

1. Usar contratos de lectura separados de la presentación. JUP-033 define
   recomendaciones y evidencia; el coste observado no se convierte en ahorro.
   Dificultad desconocida es un valor propio, no se deduce del riesgo.
2. JUP-034 entrega ahorro mensual/anual por identificador, moneda y mes base.
   El panel no anualiza ni decide qué scopes se solapan. Los totales del informe
   y sus exclusiones se preservan; no se suman importes incompatibles.
3. La demo es un doble visible de esos contratos, independiente del tenant.
   Una respuesta errónea o ausente del API nunca provoca una sustitución
   silenciosa por una demo. La dependencia propuesta no se presenta como
   una integración verificada.
4. Ahorro desconocido no equivale a cero. Importes textuales preservan precisión
   y moneda. La ordenación monetaria compara únicamente magnitudes compatibles.
5. El detalle muestra acción, justificación, riesgo, confianza, evidencia y
   condiciones. No hay botón que simule aplicar una recomendación.
6. Exportación limitada a la vista visible, con origen y unidades. Los valores
   externos no se interpolan en HTML de impresión ni se exportan como fórmulas.
7. Controles etiquetados, foco visible, texto de estado y diseño adaptable; los
   estilos globales, el shell y la marca siguen siendo responsabilidad JUP-112.

## Risks / Trade-offs

Los contratos 033/034 se inspeccionaron como propuestas locales sin commit el
10/10/2026. Se documenta el mapeo en `docs/architecture/recommendations-panel.md`.
Si cambian antes de integrarse, hay que adaptar y repetir pruebas; los dobles
no sustituyen una prueba con backend, autorización y datos reales del despliegue.

## Validation

Pruebas de filtros/orden/estados/detalle/exportación y contratos adversariales;
typecheck, lint, suite frontend, build, OpenSpec y comprobación de navegador.
Evidencia propia separada de las reviews humanas requeridas por CONTRIBUTING.
