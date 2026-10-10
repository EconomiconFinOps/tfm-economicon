# JUP-063 — Diseño de la contribución documental

## Context

Base examinada: `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
[Gobernanza](../../../docs/memoria/README.md) y [ADR-0002](../../../docs/adr/ADR-0002-litellm-openrouter.md)
conservan las decisiones existentes; no se introduce otra decisión arquitectónica.

## Decisions

1. Redacción y matriz editorial fuera de Git, sin duplicar fuente canónica.
   En Git permanecen sólo contrato, referencias y comprobaciones.
2. La evidencia del código prima frente a descripciones históricas. Se separan
   chat de plantilla, generación del processor, configuración y ejecución real.
3. Parámetros y modelos se presentan como valores de la base examinada. No se
   consultan proveedores ni se actualizan precios; los benchmarks son históricos.
4. Lectura limitada a e/g: al no disponer de esos fragmentos, no se lee la pestaña
   completa. El guion sí se contrasta por su enlace oficial.
5. La entrega propuesta es revisable antes de pedir incorporación. No se deduce
   pairing, aceptación de contenido ni revisión independiente a partir del trabajo
   automatizado. El liderazgo asignado sigue siendo de Paris.

## Validation

Lectura del flujo real, contraste de fuentes por commit y ejecución focalizada de
pruebas existentes con dobles de proveedor/almacén. No se añaden tests que se
limiten a reproducir el texto. Se registran comandos, versiones y resultados en
[la evidencia](../../../docs/evidence/JUP-063-validation.md).

## Risks and remaining work

La propuesta puede diferir del texto o estilo actual de la memoria; se reconciliará
sólo con los fragmentos autorizados. La paginación global y el PDF original no se
han validado. Tras incorporar e/g, el equipo debe exportar una versión fechada y
registrar el hash revisado; los dictámenes de contenido no se sustituyen por CI.
