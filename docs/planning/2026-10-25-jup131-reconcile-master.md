# JUP-131 — conciliación PR161 y ensayo del máster

Autorización del usuario, 25/10/2026, chat `01a15abb-d5f3-7fd3-a622-ea9e73b0db18`:
conciliar PR161 con `0edd11eff3458683553bd4c36f3011b77c1d3de4`, conservar
`ApiError` y `starlette==1.9.0`, dejar CI verde y regenerar la preparación.
No autoriza merge ni despliegue AWS.

1. Integrar la base aprobada y conservar ambas historias documentales. Restaurar
   `errors.py` y sus pruebas desde la versión aprobada. **Hecho: 0ddd59f5.**
2. Aplicar la retirada del requisito de 30 EUR únicamente a `323188184300`, con
   una política explícita sin saldo ficticio. Mantener SHA, caducidad, cuotas,
   aceptación, CI de develop y aprobación previa. Pruebas negativas y positivas.
3. Reconocer en `JUP reviews` exclusivamente la excepción PR161 ya autorizada:
   dos informes independientes, atribución real, integridad y vínculo con el
   candidato. Conservar solicitudes de cambios y reglas de cualquier otra PR.
4. Revalidar el delta mediante los dos agentes originales; publicar los informes
   sin modificar sus originales y comprobar CI técnica, SQL y política del head.
5. Regenerar configuración y solicitudes locales de ensayo con el SHA nuevo.
   La aceptación histórica no se renueva sin pruebas; CI de develop y ventana
   siguen pendientes mientras la PR esté abierta. Ningún comando de arranque.

Evidencia: `docs/evidence/JUP-131-pr161-reconciliation/`; configuración local:
`.work/master-rehearsal/`. Seguimiento en `docs/continuidad/cloud-aws.md`.
