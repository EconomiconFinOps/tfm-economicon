# Landing pública — JUP-089

Verificado: 2026-10-19. [Tarjeta](https://trello.com/c/fD7nJKRl) · [OpenSpec archivado](../../openspec/changes/archive/2026-10-19-jup-089-public-landing/) · [Evidencia](../evidence/JUP-089-validation.md).

## Alcance y decisiones

apps/landing es una aplicación estática independiente. Conserva la composición de siete secciones y demo ilustrativa aprobadas por Paris el19/10/2026. No cambia el frontend privado, autenticación o API. Se han corregido contraste/foco y color de anomalía conforme a ADR-0012, sin rediseñar. Recursos originales/licenciados, sin código HTML/JS recuperado de PR106.

## Resultado técnico local

La evaluación local original se realizó sobre f444ba11 más diff de trabajo en feat/JUP-089-public-landing. Tras aprobación de Paris, PM archivó el cambio y publicó481b4cffaf7f67607068246455834af59c14b4d8 el19/10, con fuentes funcionales idénticas y basef444 estable. Build de lista pública cerrada, manifiesto/huellas, symlinks rechazados, preview loopback con404 real y cabeceras. Sin SITE_ORIGIN se genera noindex; el origen HTTPS explícito habilita canonical/OG/sitemap coherentes. [Uso](../../apps/landing/README.md) y [operación/reversión](../operations/public-landing.md).

Pruebas focales7/7, OpenSpec82/82 y controles nativos aplicables favorables. Navegador1440/390/320, teclado/menú/demo y15muestras de contraste comprobados; medidas HTTP locales y tamaño en evidencia. Sin emulación reduced-motion ni tiempos de pintado/CWV: límites explícitos, no aceptación pública.

## Evaluación y corrección

R1 conservada: REVIEW_FAIL técnico por variables/caché de Turbo; validación local favorable sin defectos funcionales, NEEDS_CONTEXT global por criterios públicos pendientes. Tras control independiente de retorno conforme se corrigió la integración mediante configuración exclusiva de landing. R2:28pruebas afectadas PASS, tres builds raíz/orígenes/salidas externas y dev en puerto solicitado correctos; artefacto local idéntico. No hay delta de UI. R2: REVIEW_PASS técnico (21pruebas propias del Revisor) y validación funcional afectada favorable (2Turbo y dev/build propios), con aplicabilidad R1 confirmada por cada rol. NEEDS_CONTEXT global permanece. Ambos controles de integridad originales R2 conformes y recursos de evaluadores retirados; originales conservados.

## Corrección posterior de CI

El run39268057889 de481b4cf detectó dos fallos del contrato esperado de gobernanza: faltaba la línea de regresión Turbo en CI_BLOCK_TODAY. Reproducción focal2FAIL/2PASS antes de editar; corregida la lista exacta sin alterar aserciones/workflow/producto. Módulo afectado16PASS y contratoCI19PASS. Evidencia adversa conservada; nuevo delta local sobre481b4cf con evaluación independiente y nueva CI remota pendientes. No se repitieron1842casos ni UI/entornos ajenos.

## Pendientes

Archivo y commit/push previos ya autorizados y ejecutados. Pendientes: evaluación independiente del fixCI, commit/push del arreglo por PM y nueva CI remota; autorización de PR/publicación y reviews humanas. Dominio/renovación, hosting/HTTPS público y destino de demo real no están decididos; no se cierra la JUP con localhost. Direct Upload de Pages se documenta sólo como propuesta y no permite convertir el mismo proyecto a Git integration. No se ha desplegado, comprado ni modificado DNS.
