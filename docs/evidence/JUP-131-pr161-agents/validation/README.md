Paquete publicable de Validacion JUP-131

Autor: agente independiente `/root/pr161_validation`, 24/10/2026. Origen de ejecución: `.work/pr161-validation/`; no se ejecutó desde docs/evidence.

- [Informe del candidato e730](validation.md): REQUEST CHANGES por el escenario de rutas ALB reproducido después de los PASS originales.
- [Informe del delta local](delta-validation.md): PASS para los dos hashes exactos, con RED/ GREEN independiente.
- [Informe del delta Azure](azure-delta-validation.md): PASS para los dos hashes adicionales, RED de siete casos y GREEN de 82 pruebas.
- [Manifiesto de publicación](publication-manifest.json): lista completa, huellas originales/publicadas y extracciones declaradas.

Copiar este directorio completo conserva los enlaces relativos. Destino propuesto por el coordinador: `docs/evidence/JUP-131-pr161-agents/validation/`. No copiar directorios superiores, archives/tars, ejecutables, temporales ni registros iniciales grandes. No contiene credenciales reales. Los logs publicados omiten las cabeceras con rutas locales, normalizan finales de línea y sustituyen prefijos personales de Windows por `<user-home>`, cuando aparecen; cada transformación está declarada en el manifiesto. El smoke contiene un extracto literal de sus dos resultados y cierre, con auditoría íntegra de recursos aparte. El RED Azure conserva el primer fallo completo, los seis bloques de excepción HTTP y el resumen, omitiendo stacks repetidos. Las incidencias descartadas están descritas en el informe, sin presentar sus intentos como aprobaciones.
