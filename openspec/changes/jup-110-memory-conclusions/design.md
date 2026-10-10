# Diseño documental — JUP-110

## Alcance y fuentes

Sólo apartado i de la memoria. El encargo autoriza preparar su contenido; la
gobernanza JUP-062 exige revisión personal antes de publicarlo. La autorización
del apartado no se extiende a leer el documento completo. Se redacta a partir
del guion y de evidencia técnica accesible, sin abrir apartados ajenos.

Base inicial: `develop` `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
El guion se consultó directamente por el enlace de la tarjeta de coordinación
el 10/10/2026. Los resultados JUP-070 son de 08/10; su antigüedad y provisionalidad
se conservan. No se vuelven a etiquetar como pruebas ejecutadas por JUP-110.

## Decisiones

1. La propuesta y su cobertura quedan fuera del repositorio, en la raíz de
   coordinación Economicon bajo `materiales/06-entregables/JUP-110/`. No son
   exportaciones ni una segunda memoria editable. Git conserva sólo evidencia,
   contratos y su identificador de integridad.
2. Cada afirmación cuantitativa se liga a una fuente/version. Las conclusiones
   separan plantilla, embeddings y generación; pruebas de instrumento y de
   producto; ejemplo sintético y resultado de negocio observado.
3. Los requisitos de aceptación aún pendientes se presentan como tales. El
   trabajo futuro posterior no convierte obligaciones del MVP en opcionales.
4. Para incorporar se requiere el fragmento i y la guía de estilo aplicable,
   revisión humana del texto concreto y autorización de edición. Si está vacío,
   se confirma esa condición; no se obtiene contexto leyendo otros apartados.
5. La aprobación del documento se registra sobre una exportación fechada con
   SHA-256, fuera de Git. Es distinta de las reviews de la PR documental.

## Dependencias y límites

JUP-035/036 aportan el recorrido integrado, JUP-052/065 su demostración operativa,
JUP-067/070/071 la evaluación y JUP-068 el piloto de negocio. JUP-109 conserva la
sección h; JUP-063 las secciones e/g; JUP-111 la f. El contrato de intercambio es
una referencia a versión, fecha, resultados y límites: no se requiere editar
sus secciones ni esperar a sus implementaciones para preparar esta propuesta.

No se inventan pairing, aceptación, beneficios o fechas. Una nueva evidencia
posterior al corte exige revisar las conclusiones afectadas antes del cierre.
No se archiva el change mientras falten pasos del entregable.

## Verificación

Contraste de cifras con informes JSON, enlaces y separación de fuentes,
cobertura del guion y controles existentes de OpenSpec/trazabilidad/higiene.
No hay código de producto cambiado que justifique repetir sus suites o el
benchmark con llamadas de pago. La extensión global se comprueba al exportar
la memoria completa por su flujo autorizado; no se infiere del borrador local.
