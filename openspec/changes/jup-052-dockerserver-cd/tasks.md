## 1. Pipeline y agente JUP-052
- [x] 1.1 Reutilizar CI completo para validar pushes integrados a develop.
- [x] 1.2 Seleccionar exclusivamente SHA canónico actual con CD exitoso.
- [x] 1.3 Crear releases privadas aisladas y secretos locales sin sobrescritura.
- [x] 1.4 Verificar runtime antes de promoción; conservar actual ante fallo.
- [x] 1.5 Implementar rollback comprobado, pausa y exclusión mutua.

## 2. Evidencia y entrega JUP-052
- [x] 2.1 Añadir pruebas de gate, aislamiento, fallo, rollback e idempotencia.
- [ ] 2.2 Ejecutar ensayo real en DockerServer y escenarios negativos.
- [x] 2.3 Documentar instalación, acceso, operación y limitaciones.
- [ ] 2.4 Publicar evidencia y PR; coordinar roles humanos sin inventar pairing.
- [ ] 2.5 Verificar primera promoción automática tras integración y CD exitoso.
