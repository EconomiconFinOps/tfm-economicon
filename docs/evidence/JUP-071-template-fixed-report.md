# JUP-071: resultado de robustez

Ejecución: `template_mock` (`JUP-071-2aa30076f23e`). Provisional: `False`.
Robustez generativa: **no acreditada**. El endpoint no acredita qué modelo ejecutó.

Los fallos conocidos se conservan aunque falten juicios. `not_run` incluye semántica pendiente.

| Grupo | Conducta | Total | Pass | Fail | Blocked | Not run |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline | answer | 7 | 0 | 5 | 0 | 2 |
| baseline | clarify | 5 | 0 | 0 | 0 | 5 |
| baseline | abstain | 1 | 0 | 0 | 0 | 1 |
| perturbation | answer | 3 | 0 | 2 | 0 | 1 |
| perturbation | clarify | 12 | 0 | 1 | 0 | 11 |
| perturbation | abstain | 1 | 0 | 0 | 0 | 1 |

Total previsto: 29. pass / total previsto: 0,0 %. pass / (pass + fail): 0,0 %.
El denominador pass / (pass + fail) incluye fallos conocidos con juicios pendientes; no equivale a cobertura de revisión humana completa.
Casos con cobertura reducida: 0. Evaluación completa: no.

## Categorías de perturbación

| Categoría | Total | Pass | Fail | Blocked | Not run | pass / total previsto | pass / (pass + fail) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tagging | 5 | 0 | 2 | 0 | 3 | 0,0 % | 0,0 % |
| allocation | 4 | 0 | 0 | 0 | 4 | 0,0 % | no disponible |
| costs | 3 | 0 | 1 | 0 | 2 | 0,0 % | 0,0 % |
| scope | 3 | 0 | 0 | 0 | 3 | 0,0 % | no disponible |
| anomalies | 1 | 0 | 0 | 0 | 1 | 0,0 % | no disponible |

## Tipos de perturbación

| Tipo | Pass | Fail | Blocked | Not run |
| --- | ---: | ---: | ---: | ---: |
| missing_tag_with_sufficient_allocation_rule | 0 | 0 | 0 | 1 |
| null_tag_value | 0 | 1 | 0 | 0 |
| empty_and_whitespace_tag_values | 0 | 1 | 0 | 0 |
| unknown_controlled_tag_value | 0 | 0 | 0 | 1 |
| conflicting_tags_after_key_normalization | 0 | 0 | 0 | 1 |
| missing_shared_weights | 0 | 0 | 0 | 1 |
| ambiguous_shared_weight_units | 0 | 0 | 0 | 1 |
| missing_eligible_cost_denominator | 0 | 0 | 0 | 1 |
| confirmed_zero_denominator | 0 | 0 | 0 | 1 |
| missing_business_volume_denominator | 0 | 1 | 0 | 0 |
| partial_vs_complete_period | 0 | 0 | 0 | 1 |
| ambiguous_date_format | 0 | 0 | 0 | 1 |
| missing_currency_unit | 0 | 0 | 0 | 1 |
| incompatible_time_units | 0 | 0 | 0 | 1 |
| empty_result_with_incomplete_ingestion | 0 | 0 | 0 | 1 |
| unavailable_real_tenant_with_synthetic_decoy | 0 | 0 | 0 | 1 |

## Casos

| Caso | Resultado | Juicios pendientes | Cobertura reducida | Eco del prompt |
| --- | --- | ---: | --- | --- |
| JUP-069-002 | fail | 3 | False | True |
| JUP-069-003 | not_run | 4 | False | True |
| JUP-069-005 | fail | 6 | False | True |
| JUP-069-008 | not_run | 5 | False | True |
| JUP-069-009 | not_run | 4 | False | True |
| JUP-069-010 | not_run | 4 | False | True |
| JUP-069-011 | fail | 3 | False | True |
| JUP-069-012 | not_run | 4 | False | True |
| JUP-069-016 | fail | 4 | False | True |
| JUP-069-023 | not_run | 5 | False | True |
| JUP-069-024 | not_run | 5 | False | True |
| JUP-069-026 | not_run | 4 | False | True |
| JUP-069-027 | fail | 4 | False | True |
| JUP-071-001 | not_run | 6 | False | True |
| JUP-071-002 | fail | 6 | False | True |
| JUP-071-003 | fail | 6 | False | True |
| JUP-071-004 | not_run | 6 | False | True |
| JUP-071-005 | not_run | 6 | False | True |
| JUP-071-006 | not_run | 6 | False | True |
| JUP-071-007 | not_run | 6 | False | True |
| JUP-071-008 | not_run | 6 | False | True |
| JUP-071-009 | not_run | 6 | False | True |
| JUP-071-010 | fail | 6 | False | True |
| JUP-071-011 | not_run | 6 | False | True |
| JUP-071-012 | not_run | 5 | False | True |
| JUP-071-013 | not_run | 6 | False | True |
| JUP-071-014 | not_run | 6 | False | True |
| JUP-071-015 | not_run | 6 | False | True |
| JUP-071-016 | not_run | 6 | False | True |

Identidad y parejas completas en el JSON asociado. Sin textos de respuestas ni nombres de revisores.
