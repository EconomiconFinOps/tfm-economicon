## 1. Aplicación pública

- [x] 1.1 Incorporar el diseño aprobado con assets locales y atribuciones en app separada
- [x] 1.2 Conservar navegación, siete secciones, perspectivas y demo simulada; corregir contraste/foco/semántica
- [x] 1.3 Añadir metadatos, OG/favicon, robots/sitemap y404 sin URLs públicas inventadas

## 2. Frontera y operación

- [x] 2.1 Build de lista cerrada, hashes y rechazo de symlinks; ninguna fuente privada publicada
- [x] 2.2 Preview loopback con cabeceras, rutas/métodos limitados y404 real
- [x] 2.3 Documentar publicación preparada, dominio/renovación/HTTPS pendientes y rollback reproducible

## 3. Evidencia

- [x] 3.1 Pruebas focales del build/servidor/SEO y controles nativos obligatorios aplicables
- [x] 3.2 Recorrido visual1440/390/320, teclado, movimiento reducido y medidas locales
- [x] 3.3 Matriz de criterios oficiales con estado real y límites; actualizar continuidad

## 4. Revisión y cierre

- [x] 4.1 Candidato fijo, referencias originales y revisión/validación independientes locales con límites
- [x] 4.2 Atender hallazgos y repetir evaluación afectada (P2 de Turbo resuelto en R2; fix posterior del contrato CI con revisión y validación locales afectadas favorables)
- [x] 4.3 Aprobación humana posterior a validación y archivo autorizado en la misma rama (Paris, 19/10/2026)
- [ ] 4.4 Publicación autorizada, CI y reviews humanas; dominio/hosting/HTTPS públicos cuando se autoricen

Nota del 19/10/2026: las tareas locales marcadas conservan el alcance y límites de la evidencia: reduced-motion estático, métricas HTTP/tamaño y DOM, sin tiempos de pintado/CWV ni auditoría pública. Dominio, HTTPS/despliegue públicos y cierre humano permanecen pendientes; no se declaran cumplidos por estas casillas.

Cierre local19/10: originales R1/R2 conservados, ambos retornos de integridad conformes y cada evaluador confirma aplicabilidad de la evidencia no afectada. Paris autoriza el archivo, commit y push tras la entrega evaluada; archivado en la misma rama el19/10. NEEDS_CONTEXT global permanece para los criterios públicos; 4.4 continúa pendiente.

Corrección posterior del19/10 sobre481b4cf: falloCI de expectativa literal reproducido2FAIL/2PASS, lista exacta actualizada y16+19pruebas focales conformes. La casilla4.2 se reabre sólo para la evaluación independiente afectada del fix, conservando resultados R1/R2. Archivo/commit/push previos autorizados y ejecutados; nueva publicación del arreglo corresponde al PM.

Delta21/10: reconciliación local c227+bc94 y observaciones de reviews preparadas.
Enlaces docs/repositorio, alcance integrado/simulado/pendiente, HSTS probado y
contraste corregido conservando diseño. Mediciones locales y reversión:
[evidencia actual](../../../../docs/evidence/JUP-089-validation.md#reconciliación-y-observaciones-de-las-reviews--21102026).
La evaluación independiente de este delta está pendiente en este corte; no se
reabre ni se archiva otro change. 4.4 sigue pendiente y los límites públicos
anteriores no se convierten en PASS por los resultados locales.


## Reconciliación posterior — 22/10/2026

PR142 se reconcilia localmente desde c684210275e2788de2c660b52cf3ad8098d7fd32 con develop c00063dbaa83a1237431edef9de6d71d1bfd1ffd sin commit; único conflicto documental conserva ambas filas. Diseño, 20 fuentes de app, contratos y artefacto c684 intactos. 46 pruebas focales, builds raíz y 13 peticiones reales favorables, con registros separados. Se conservan fixes publicados y todo feedback anterior; no se cambia ni rearchiva esta especificación. Véase la [matriz vigente](../../../../docs/evidence/JUP-089-validation.md#estado-vigente-delta-local-c684--c000--22102026).

Revisión y validación independientes del candidato fijo requieren nuevas referencias originales y conservan los límites. La tarea4.4 sigue pendiente: resultados locales y pairing documentado sobre c227 no equivalen a reviews humanas afectadas, CI nueva o aceptación pública. Dominio/renovación, alojamiento/DNS/HTTPS/despliegue/reversión públicos, vídeo y destino auténtico de demo siguen pendientes; reduced-motion interactivo NOT_VALIDATED, límite aceptado y explícito. No se autoriza commit/push/publicación o merge por esta reconciliación. El liderazgo mostrará informe y borrador antes de subir nada.


## Incremento de base para publicación — 22/10/2026

R1 local sobre c684+c000 terminó con revisión y validación focales favorables; el liderazgo lo conservó como commit local c72f99f47eff36b72d6a51df4b314f3f33dab0af. Paris autoriza subir, comprobar CI y solicitar a Lucía revalidación sólo del delta. Se incorpora develop4567e8e7667c3fa5ad2d17eedd2f3da7a332e4bb/PR151 sin commit todavía de esta segunda integración; el conflicto de índice conserva ambas filas y todos los cambios entrantes. Las 20 fuentes de landing,11contratos y entradas de pruebas R1 mantienen identidad; reutilización explícita de46pruebas/builds/HTTP/UI/Lighthouse, sin baterías nuevas. Se ejecutan sólo controles documentales afectados; los mismos evaluadores emiten adendas independientes con referencias nuevas, sin sustituir originales. Véase el [incremento vigente](../../../../docs/evidence/JUP-089-validation.md#incremento-vigente-para-publicación--22102026).

Sin cambios de producto, requisitos o rearchivo. La tarea4.4 y los requisitos humanos/públicos conservan su alcance; aprobaciónLucía c227 dismissed es histórica, pairingVíctor c227 preservado y reduced-motion interactivo NOT_VALIDATED aceptado. Autorización de publicación no acredita CI del SHA futuro, aceptación pública o merge. Git/publicación a cargo del liderazgo.
