# Memoria de IA — JUP-063

Verificado el 10/10/2026. Encargo: «Implementa JUP-063 — Redactar memoria de IA»;
recibido del chat coordinador `01a1248a-4e9e-7963-a891-5d8cb49345a6`.
[Tarjeta](https://trello.com/c/sRKGpYEy), id `69da4531119a60549856c34a`.
[PR #95 en borrador](https://github.com/EconomiconFinOps/tfm-economicon/pull/95),
contra `develop`; revisión, validación e incorporación canónica pendientes.

## Alcance y decisiones

- Sólo e/g, conforme a [gobernanza](../memoria/README.md). No modifica contenido
  de JUP-109, JUP-110 ni JUP-111. Fuente canónica: Google Docs, localizada por
  la tarjeta de enlaces; no se copia su cuerpo ni su URL a esta continuidad.
- Rama propia `docs/JUP-063-memoria-ia`, creada desde `origin/develop`
  `c2995a118d419dfe725247bac9c6f219a3f0ea77`; worktree
  `tfm-economicon-jup063` junto al checkout compartido, que permanece intacto.
  No se encontró una rama o PR propia de JUP-063 antes de empezar.
- PR85 de gobernanza ya integrada en la base: la nota local anterior que la
  describía abierta está superada por ese hecho, sin rehacer su historial.
- Código confirmado: chat con embeddings/recuperación/citas y respuesta de
  plantilla; análisis generativo separado en la ingesta y sin chunks en el
  prompt. Guardas validan estructura, no veracidad material. No se atribuye
  fine-tuning, calidad semántica al mock ni generación real al chat.
- [Evidencia y criterios](../evidence/JUP-063-validation.md) y
  [contrato del cambio](../../openspec/changes/jup-063-ai-memory/proposal.md).

## Entrega externa y límites

Propuesta original para revisión humana, **no export de la memoria**, en el
workspace de coordinación, fuera de Git:
`materiales/06-entregables/JUP-063-2026-10-10/propuesta-ia-e-g.md`.
Contiene E1–E9/G1–G5, referencias fijadas al commit y cobertura de las tres
partes del guion. Logs y manifiesto:
`materiales/07-evidencias/JUP-063-2026-10-10/`.

Se leyó `Guion_PJ.md` por su enlace de la integración oficial, no otras entradas
de la carpeta. No se comprobó el PDF original. De la memoria sólo se consultó
metadata de pestañas: el conector no permite limitar texto por sección dentro
de la única pestaña. Se solicitaron fragmentos e/g y guía de estilo; no se leyó
el cuerpo ni se escribió en Google Docs. La redacción independiente no prueba
su reconciliación con el documento ni el máximo de 20 páginas.

Roles confirmados por DockerServer el 10/10: Paris liderazgo, Victor pairing,
Alejandro revisión y Lucia validación. La contribución se prepara en rama
propia para Paris; la cuenta GitHub disponible `Iber1to` no se presenta como
pairing ni dictamen independiente. No se cambian roles, prioridad ni fechas.

## Verificación de la contribución

28 fuentes fijadas a la base, 19 enlaces locales, 56 elementos OpenSpec y
trazabilidad correctos; 7 tests de gateway correctos. Suites Python locales:
353 PASS / 11 FAIL / 6 SKIP. Los fallos están acotados a plazos de servidores
HTTP de loopback y subprocesos auxiliares de pruebas; su causa raíz queda sin
resolver y no se oculta ni se atribuye a Python 3.14 por inferencia.
Detalle, versiones y comandos en la evidencia. No se probó SQL real ni LLM real.

## Próximos pasos

1. Paris revisa el texto propuesto y facilita e/g y guía de estilo para resolver
   diferencias antes de incorporar. La norma prohíbe publicar sin revisión humana.
2. Incorporación autorizada exclusivamente de e/g al documento canónico;
   comprobar referencias y paginación conjuntamente, sin editar otros apartados.
3. Exportar la versión acordada fuera de Git y registrar fecha/SHA-256. Distinguir
   la revisión del contenido de la revisión de la PR de evidencia.
4. Completar participación real y dictámenes independientes; no cerrar JUP-063
   ni archivar OpenSpec mientras esos pendientes sigan abiertos. La cuenta que
   aporte esta PR no puede emitir su dictamen independiente sobre ella.
5. Reproducir los once fallos de tests en un entorno controlado compatible con
   CI; no declarar verde global a partir de los controles documentales.
