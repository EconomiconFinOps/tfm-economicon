# Filtros operativos de costes — JUP-056

[Tarjeta](https://trello.com/c/4AbHqWKW). Extensión aditiva de `GET /billing/summary`
v2 sobre costes normalizados almacenados. No modifica el contrato del simulador
Azure Query ni requiere llamar a Azure desde el frontend.

| Parámetro opcional | Significado |
| --- | --- |
| `subscription_id` | Cuenta como ID de suscripción Azure |
| `service_name` | Servicio normalizado, con coincidencia exacta |
| `project` | Proyecto tipado o, cuando falta, etiqueta normalizada `project` |
| `filter_tag_key` | Clave de etiqueta; normalización y aliases de `tag_key` |
| `filter_tag_value` | Valor exacto de la etiqueta; obligatorio junto a la clave |

Los filtros se combinan mediante AND antes de agregar, tanto en los totales
como en los grupos. Los valores son sensibles a mayúsculas y preservan espacios
significativos. Se rechazan valores vacíos, sólo espacios, controles ASCII/DEL,
claves sin caracteres válidos y parejas de etiqueta incompletas (422). `tag_key`
sigue siendo sólo la clave de agrupación cuando `group_by=tag`; puede diferir
de `filter_tag_key`. Los parámetros se codifican como URL y se enlazan en SQL.

Ejemplo (cabeceras de sesión/tenant gestionadas por la capa API existente):

```http
GET /billing/summary?start_date=2024-06-01&end_date=2024-07-01&group_by=service&subscription_id=sub-a&service_name=Compute&project=Typed&filter_tag_key=env&filter_tag_value=Prod
```

Además de los campos v2, una respuesta filtrada añade:

```json
{"filters":{"subscription_id":"sub-a","service_name":"Compute","project":"Typed","filter_tag_key":"environment","filter_tag_value":"Prod"}}
```

Sólo se incluyen claves solicitadas y la clave de etiqueta es canónica. Sin
filtros no se añade `filters`, conservando la forma original para ejecutivo y
otros consumidores. La pantalla verifica periodo, agrupación y metadata; un
backend anterior que ignore filtros produce un error visible, nunca totales
globales rotulados como filtrados.

Se mantiene el periodo UTC `[start_date, end_date)`, `contract_version=2`, los
importes como strings decimales y la separación por moneda. El redondeo de cada
grupo puede hacer que su suma difiera del total, calculado independientemente.
Sin coincidencias se devuelven listas vacías, sin un cero financiero inventado.

El tenant se autoriza antes de consultar costes. La detección de fuentes
solapadas sigue cubriendo tenant/periodo completos antes de filtrar (409); no
se puede ocultar una fuente ambigua mediante un filtro. `missing_dimension_count`
corresponde a los registros filtrados, pero `excluded_undated_count` mantiene
su significado anterior para todo el tenant y puede causar `partial` incluso
sin coincidencias. Los indicadores de ingesta conservan su alcance previo.

La UI no ofrece filtrar explícitamente por dimensión ausente en esta entrega.
Los campos vacíos significan no aplicar ese filtro. Un catálogo/autocompletado,
paginación de desglose y soporte de otros proveedores quedan fuera del alcance
de esta extensión; no se declara su implementación.
