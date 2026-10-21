# JUP-131 — compatibilidad PostgreSQL local

Verificado el 21/10/2026, implementación de adaptaciones autorizada por el usuario.
No es evidencia de RDS desplegado ni aceptación funcional completa AWS.

## Cambio y pruebas

Los validadores de ambos servicios admiten PostgreSQL operativo sin retirar
Cockroach ni el límite de conexión local insegura. DDL nuevo usa TEXT, compatible
con ambos motores; no hay ALTER de tipos de datos existentes. La comprobación
de restricciones contempla el catálogo PostgreSQL (ANY/ARRAY y BETWEEN
decompuesto), conservando rechazo de condiciones añadidas y estados extra.
Los CAST de la consulta de facturación usan TEXT.

`tools/aws_demo/test_postgresql.py` crea bases de nombre aleatorio exclusivamente
en una instancia de pruebas explícita. Rechaza DSN ajenos al contrato local de
pruebas. Ejecuta backend, processor y todas las migraciones pgvector, dos veces;
comprueba versiones, identidad, membresías, coste EUR12.50 e inexistencia de
costes de ese fixture en otro tenant. Elimina únicamente sus propias bases.

Se observó RED por rechazo del DSN y tipo STRING inexistente, después por
representación de restricciones y CAST de costes. Tras cambios incrementales,
GREEN: 1 integración completa PASS en PostgreSQL16/pgvector. El contenedor
deshechable no monta volúmenes existentes. Imagen de prueba:
`pgvector/pgvector:pg16@sha256:7b822b0aac60967beb1ea5e576b8602c94c300a157d187f385ae3e0da199b90a`.
La CI añade `AWS PostgreSQL application` para repetir el contrato en Linux.

Regresión focal: backend94PASS/6omitidas y processor69PASS/6omitidas (omitidas
requieren otro contrato de integración, no se cuentan como aprobadas).
Cockroach24.1.11 real: 50PASS en esquema/chat/reconciliación; cuatro controles de
resumen inicialmente fallaron por entorno local (tokenizers0.23.1 y recurso
tokenizer ausente). Con venv aislado y dependencias fijadas0.22.1, más el tokenizer
verificado por el instalador del proyecto: 4PASS. No se debilitó la política de
recursos para obtener ese resultado.

Comando de integración, con DSN sintético de una instancia desechable propia en
`AWS_POSTGRES_TEST_URL`: `python -m unittest tools.aws_demo.test_postgresql -v`.
Logs locales ignorados: `.work/aws-application/postgresql-billing-green.log`,
`cockroach-regression.log`, `summary-native.log` y regresiones focales.

## Pendiente

RDS/TLS real, usuarios con privilegios mínimos, bootstrap, fixture completo del
guion, Cognito y Bedrock se verifican por separado. Los resultados de aquí no
permiten marcar el ensayo AWS como desplegable ni habilitar aplicación Terraform.
