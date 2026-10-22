# JUP-131 — correcciones de revisión PR146

22/10/2026. Autorización: corregir las solicitudes de la revisión y comprobar
CI. No desplegar en AWS. Base: bee31eca11a3c0ffe4fda4a77e8c89b8165b30d3.

1. Probar y limitar el plan applications a direcciones ECS/políticas Bedrock
   conocidas, sin borrados ni sustituciones; vincular clase de plan al recibo.
2. Exigir CI push/develop y pertenencia del SHA a develop antes de provisionar.
3. Transiciones de lease con compare-and-swap de fase y configuración.
4. Entorno permitido explícitamente y HOME separado para compilación/pruebas,
   sin tokens, contraseñas ni cadenas de credenciales AWS heredadas.
5. Registrar tareas devueltas antes de validar; cancelar las del propio clúster
   incluso ante respuesta inválida, preservando la exclusión de recursos ajenos.
6. Rechazar credenciales reconocibles dentro de valores públicos, recursivamente.
7. Exigir contrato completo y coherente Bedrock/Titan/Nova en la receta.
8. Limitar consultas JWKS, incluidos fallos, con rotación y concurrencia acotadas.

Añadir regresiones primero y observar su fallo; después ejecutar suites locales,
revisión técnica independiente y CI del SHA publicado. Normalizar errores de
tipos y dígitos ASCII donde la revisión los señala. Conservar los dictámenes
humanos pendientes: las pruebas y la revisión técnica no los sustituyen.
