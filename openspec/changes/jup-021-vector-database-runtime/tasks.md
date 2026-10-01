## 1. Implementacion
- [x] 1.1 Reutilizar imagen y crear Compose aislado persistente.
- [x] 1.2 Agregar indice tenant mediante migracion incremental.
- [x] 1.3 Rechazar dimensiones incompatibles sin destruir documentos.
- [x] 1.4 Crear smoke de escritura, retrieval y aislamiento reales.

## 2. Validacion y operacion
- [x] 2.1 Verificar arranque limpio y migraciones repetibles.
- [x] 2.2 Verificar persistencia tras recrear contenedor.
- [x] 2.3 Restaurar copia en volumen separado y repetir retrieval.
- [x] 2.4 Ejecutar regresion y validadores de repositorio.
- [x] 2.5 Documentar capacidad, modelo, recuperacion y diagnostico.
- [ ] 2.6 Vincular PR, revision humana y validacion del equipo antes del cierre.

## 3. Correcciones de validacion del 1 de octubre
- [x] 3.1 Conservar diagnostico de dimension mediante StartupError en los arranques.
- [x] 3.2 Cubrir esquema mayor, menor, no restringido y coincidente en CI.
- [x] 3.3 Verificar ambos desajustes e indexdef en el smoke real.
- [x] 3.4 Registrar RF-021-001 y actualizar runbook/evidencia sin rutas personales.
- [ ] 3.5 Obtener aceptacion de Victor sobre las correcciones antes del cierre.
