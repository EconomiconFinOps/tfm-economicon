# PR121: compatibilidad del esquema de evidencia

12/10/2026. Encargo del usuario: «Hazlo», tras autorizar validación sintética en
OpenRouter GLM5.2/DeepInfra, máximo adicional0.50USD sin renovar claves ni límites.
Código publicado: e56562f, rama propia fix/JUP-035-auto-documentation.

## Cambio

Se omite uniqueItems únicamente en la proyección de evidencia del proveedor.
Se conservan alternativas exactas id/kind/title/source, abstención sin fuentes,
HMAC, número de llamadas y rechazo independiente de duplicados en Pydantic
processor y firewall backend. Contrato efectivo-context-exact-records-v2 y hash
sincronizados; no cambia el esquema público FinOpsResponse.

## Verificación

- Backend evidencia+auto:20PASS. Processor recursos/gateway/auto:86PASS.
  La ejecución inicial local de evidencia falló por permisos de temporales;
  repetición fuera del sandbox12PASS, incluida en las20, no sumarla.
- OpenSpec67/67. Build backend/processorPASS. Hashes de75/69 archivos Python
  activos coinciden con el snapshot corregido. Un primer build detectó hash
  backend sin actualizar; corregido antes de activar y enviar inferencias.
- JUP-069-018 focal:completed, una búsqueda HMAC, streaming y persistencia.
  El esquema efectivo con fuentes es aceptado. La respuesta calcula200EUR/día
  y20%, pero afirma la regla documental sin citations/evidence: fallo semántico,
  no aceptación global. No se confunde completed con calidad aprobada.
- Saludo focal:completed sin búsqueda ni evidencia fabricada. El harness heredó
  mojibake en los caracteres españoles del saludo; limita este ensayo y requiere
  contraste desde UI con texto correcto. El banco JUP-069 se lee JSON remoto.
- Navegador localhost:login e historial del saludo persistido verificados.
  Envío posterior desde UI con texto correcto: respuesta terminada, recarga y
  reapertura con pregunta/respuesta persistidas. Sin nuevo error visible.

## Pendientes independientes

Las llamadas múltiples siguen rechazándose sin ejecutar herramientas extra.
La revisión de Víctor del12/10 17:58UTC pide cambios en dos carreras de streaming,
truncación de decisión, emoji de un fixture, conflicto documental con develop y
provisión CHAT_HMAC_FILE en CD. Leída íntegramente; no resuelta por este parche.
No merge, aprobación propia, cambio a la rama de Paris ni Discord.

Recibos locales: materiales/07-evidencias/PR121-herramientas-evidencia-20261012/
compat-focused.json, compat-full28.json, compat-diagnostic.log, build-compat.log,
compat-activate.log. El resumen de resultados queda aquí para revisión sin
necesitar acceso a esas rutas locales.

En esta muestra001 devuelve1000EUR y60% como ejercicio hipotético; mejora frente
al corte anterior, sin prueba de estabilidad.010 recupera la política de cinco
tags y devuelve dos referencias exactas de corpus con persistencia de un par.
Estos resultados no compensan el fallo de citas de018 ni la multiplicidad.

## Campaña completa posterior

Con extensión de claves expresamente autorizada, se han ejecutado los28casos.
[Resultado vigente:23completed/5failed y defectos semánticos](jup-035-pr121-full28-20261012.md).
El corte parcial siguiente se conserva como histórico.

## Resultado final de campaña parcial

Batería detenida por la guarda horaria a las18:24UTC, antes de caducidad18:25UTC:
19/28 ejecutados en orden, cada uno un intento;15completed y4failed. Fallan003,
005,006,008 con native_multiple_calls.020–028 NOT_RUN, no contarlos como fallos
ni aprobados. La excepción AssertionError del harness representa esa guarda,
no una aserción de producto.018 completó también en esta batería, esta vez con
la cita rules:chunk:7; el focal anterior sin cita queda conservado y demuestra
variabilidad. No se selecciona sólo la respuesta favorable.

CI del código e56562f: seis checks técnicos PASS; JUP policy SKIPPED en push.
Run38290037946: https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38290037946
No sustituye las reviews oficiales ni resuelve el conflicto con develop.

Gasto acumulado observado desde la autorización específica: claves processor
0.0856426375→0.13945123USD y backend0.00000688→0.00001118USD; incremento conjunto
0.0538128925USD, menor que0.50USD. OpenRouter compartido0.134890510→0.189956182USD,
no factura exclusiva. Sin renovación/ampliación. Runtime detenido y recibos
preservados. Este parche corrige la compatibilidad; aceptación globalNO PASS.

Próximo paso: atender las peticiones de Víctor y la multiplicidad, estabilizar
citas documentales y completar020–028 más validación final con claves vigentes.
La autorización actual no permite renovar las claves caducadas.
