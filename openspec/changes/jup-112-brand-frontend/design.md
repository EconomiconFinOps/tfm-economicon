# JUP-112 — Identidad visual del frontend

Trello: https://trello.com/c/XTZU3vj3

## Fuentes y límites

Tarjeta contrastada el 2026-10-10 mediante la integración desplegada en
DockerServer. Dossier existente `materiales/05-marketing/economicon_dossier.pptx`
en el workspace de coordinación, diapositivas 5–7; procedencia y hashes en
`docs/frontend-brand.md`. La tarjeta PROYECTO no devuelve adjuntos o enlaces de
marca en esta consulta, por lo que se utiliza el dossier local ya existente.

## Decisiones

1. Conservar el sistema semántico de [ADR-0012](../../../docs/adr/ADR-0012-frontend-color-tokens.md)
   y sustituir su elección visual oscura por una paleta clara única. No se añade
   selector de tema. La revisión propuesta del ADR identifica esta evolución;
   no atribuye ratificación humana. Continúan ADR-0003 (TypeScript) y ADR-0004
   (primitivos shadcn copiados).
2. Índigo para identidad y navegación, blanco roto predominante, lila en
   superficies suaves. Violeta limitado a acciones; coral para ahorro/insights
   acompañado de texto oscuro. Estados y gráficas pueden usar tonos derivados
   legibles: la tarjeta permite criterio de diseño.
3. Tipografías servidas por el bundle desde paquetes con licencia OFL. Evitar
   peticiones a Google Fonts o servicios de terceros durante el uso.
4. Extraer bytes originales de los dos PNG del dossier. No redibujar ni producir
   un logotipo parecido. Componente compartido con alternativa textual apropiada
   para uso en cabecera/login y reutilización posterior por la landing.
5. Mantener contenido y contratos funcionales. Los cambios de responsive se
   limitan a distribución, tamaño y desplazamiento contenido de datos anchos.

## Coordinación por contratos

- JUP-099: tokens, alias, ausencia de literales y guardianes se conservan.
- JUP-056/JUP-058: consumir tokens semánticos, `chartTheme` y componentes
  compartidos; conservar sus rutas/hooks/tablas/API. Reconciliar únicamente
  cambios de clases si sus ramas se integran después.
- JUP-089: reutilizar BrandMark y fuentes/tokens locales. No crear una segunda
  paleta ni copiar logotipos a otra fuente. Su ruta/contenido no se implementan aquí.
- Ningún mensaje a otros chats o miembros constituye pairing o validación.

## Verificación

Suite frontend serial, typecheck/lint/build, OpenSpec y gobernanza aplicable.
Navegador real con API simulada: pantallas actuales, escritorio y móvil,
tipografías, foco, desbordamientos y estados de error/carga. Evidencia propia
separada de `Revision JUP-112` y `Validacion JUP-112`, pendientes del equipo.
