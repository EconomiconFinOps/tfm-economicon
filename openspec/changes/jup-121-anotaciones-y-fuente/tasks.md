## 1. Anotaciones y fuente

- [x] 1.1 Aplicar la capa «Cambios de configuración» a la evolución de la latencia (D1), con prueba en Grafana real del escenario de Paris (dos pares comparables y un cambio de batería) y parche a la prueba congelada que fija exactamente los paneles anotados
- [x] 1.2 «Estado de los casos por ejecución» solo de JUP-070 (D2), con prueba contra PostgreSQL real con una ejecución de otra fuente y recuentos de casos

## 2. Documentación y cierre

- [x] 2.1 Contrato de clasificación para nuevas fuentes en la guía (D3) y nota de que el panel de robustez se hará con el informe de JUP-071
- [x] 2.2 Validación (`evaluation-dashboard:test`, `openspec:validate`, `jup:check`, `jup:cleanup:check`), `review.md` y evidencia en `docs/evidence/JUP-121-validation.md`
