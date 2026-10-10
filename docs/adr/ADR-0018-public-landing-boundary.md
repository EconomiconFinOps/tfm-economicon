# ADR-0018: Landing estática separada de la aplicación privada

- Status: Proposed
- Date: 2026-10-10
- Related JUP/OpenSpec: JUP-089, [public-landing](../../openspec/changes/jup-089-public-landing/design.md)
- Trello: https://trello.com/c/fD7nJKRl
- Supersedes: none
- Superseded by: none

## Contexto

La comunicación pública necesita enseñar marca, propuesta FinOps y evidencia sin
abrir la aplicación, sus sesiones, tenants o infraestructura. M4 funcional y M5 RC1
no quedan acreditados por el trabajo de esta tarjeta. JUP-112 adapta la marca del
frontend privado en paralelo.

## Decisión propuesta

Publicar un artefacto HTML/CSS autónomo producido por `apps/landing`, servido en la
raíz de un origen público independiente. No compartir bundles, configuración de
API, credenciales, cookies ni rutas con `apps/frontend`. El build selecciona las
fuentes públicas y genera metadatos según un origen aprobado explícitamente.

El servidor Node incluido es únicamente una preview de loopback. El hosting final
debe terminar HTTPS y aplicar el contrato de cabeceras y 404 descrito en el runbook.
No se escoge proveedor ni dominio ni se despliega en DockerServer con este ADR.

## Alternativas y consecuencias

- Una ruta pública en la SPA existente aumenta el acoplamiento con sesión y build
  privado, y mezcla este cambio con JUP-112; no aporta valor al contenido estático.
- Un CMS o framework adicional añade dependencias y operación innecesarias para
  esta página. HTML/CSS y Node permiten builds y pruebas sin runtime de terceros.
- Mantener el sitio aparte exige actualizar sus afirmaciones cuando cambie el
  producto. La procedencia y la separación entre integrado/simulado/futuro reducen
  ese riesgo. La aprobación editorial sigue siendo responsabilidad del equipo.

Estado Proposed hasta revisión atribuible; implementación o CI no equivalen a
aceptación humana ni a autorización de publicación del dominio.
