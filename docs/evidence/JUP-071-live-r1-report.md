# JUP-071: resultado de robustez

Ejecución: `live_unverified` (`JUP-071-a543144c9a55`). Provisional: `True`.
Robustez generativa: **no acreditada**. El endpoint no acredita qué modelo ejecutó.

Los fallos conocidos se conservan aunque falten juicios. `not_run` incluye semántica pendiente.

| Grupo | Conducta | Total | Pass | Fail | Blocked | Not run |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline | answer | 7 | 2 | 4 | 1 | 0 |
| baseline | clarify | 5 | 1 | 2 | 2 | 0 |
| baseline | abstain | 1 | 1 | 0 | 0 | 0 |
| perturbation | answer | 3 | 2 | 1 | 0 | 0 |
| perturbation | clarify | 12 | 1 | 9 | 2 | 0 |
| perturbation | abstain | 1 | 0 | 1 | 0 | 0 |

Total previsto: 29. pass / total previsto: 24,1 %. pass / (pass + fail): 29,2 %.
El denominador pass / (pass + fail) incluye fallos conocidos con juicios pendientes; no equivale a cobertura de revisión humana completa.
Casos con cobertura reducida: 24. Evaluación completa: no.

## Categorías de perturbación

| Categoría | Total | Pass | Fail | Blocked | Not run | pass / total previsto | pass / (pass + fail) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tagging | 5 | 2 | 3 | 0 | 0 | 40,0 % | 40,0 % |
| allocation | 4 | 0 | 3 | 1 | 0 | 0,0 % | 0,0 % |
| costs | 3 | 0 | 3 | 0 | 0 | 0,0 % | 0,0 % |
| scope | 3 | 1 | 1 | 1 | 0 | 33,3 % | 50,0 % |
| anomalies | 1 | 0 | 1 | 0 | 0 | 0,0 % | 0,0 % |

## Tipos de perturbación

| Tipo | Total | Pass | Fail | Blocked | Not run |
| --- | ---: | ---: | ---: | ---: | ---: |
| missing_tag_with_sufficient_allocation_rule | 1 | 1 | 0 | 0 | 0 |
| null_tag_value | 1 | 1 | 0 | 0 | 0 |
| empty_and_whitespace_tag_values | 1 | 0 | 1 | 0 | 0 |
| unknown_controlled_tag_value | 1 | 0 | 1 | 0 | 0 |
| conflicting_tags_after_key_normalization | 1 | 0 | 1 | 0 | 0 |
| missing_shared_weights | 1 | 0 | 1 | 0 | 0 |
| ambiguous_shared_weight_units | 1 | 0 | 1 | 0 | 0 |
| missing_eligible_cost_denominator | 1 | 0 | 1 | 0 | 0 |
| confirmed_zero_denominator | 1 | 0 | 0 | 1 | 0 |
| missing_business_volume_denominator | 1 | 0 | 1 | 0 | 0 |
| partial_vs_complete_period | 1 | 0 | 1 | 0 | 0 |
| ambiguous_date_format | 1 | 0 | 1 | 0 | 0 |
| missing_currency_unit | 1 | 0 | 0 | 1 | 0 |
| incompatible_time_units | 1 | 0 | 1 | 0 | 0 |
| empty_result_with_incomplete_ingestion | 1 | 1 | 0 | 0 | 0 |
| unavailable_real_tenant_with_synthetic_decoy | 1 | 0 | 1 | 0 | 0 |

## Casos

| Caso | Resultado | Juicios pendientes | Cobertura reducida | Eco del prompt |
| --- | --- | ---: | --- | --- |
| JUP-069-002 | fail | 0 | True | False |
| JUP-069-003 | blocked | 0 | False | False |
| JUP-069-005 | fail | 0 | True | False |
| JUP-069-008 | blocked | 0 | False | False |
| JUP-069-009 | fail | 0 | True | False |
| JUP-069-010 | blocked | 0 | False | False |
| JUP-069-011 | pass | 0 | True | False |
| JUP-069-012 | pass | 0 | True | False |
| JUP-069-016 | fail | 0 | True | False |
| JUP-069-023 | pass | 0 | True | False |
| JUP-069-024 | fail | 0 | True | False |
| JUP-069-026 | pass | 0 | True | False |
| JUP-069-027 | fail | 0 | True | False |
| JUP-071-001 | pass | 0 | True | False |
| JUP-071-002 | pass | 0 | True | False |
| JUP-071-003 | fail | 0 | True | False |
| JUP-071-004 | fail | 0 | True | False |
| JUP-071-005 | fail | 0 | True | False |
| JUP-071-006 | fail | 0 | True | False |
| JUP-071-007 | fail | 0 | True | False |
| JUP-071-008 | fail | 0 | True | False |
| JUP-071-009 | blocked | 0 | False | False |
| JUP-071-010 | fail | 0 | True | False |
| JUP-071-011 | fail | 0 | True | False |
| JUP-071-012 | fail | 0 | True | False |
| JUP-071-013 | blocked | 0 | False | False |
| JUP-071-014 | fail | 0 | True | False |
| JUP-071-015 | pass | 0 | True | False |
| JUP-071-016 | fail | 0 | True | False |

Identidad y parejas completas en el JSON asociado. Sin textos de respuestas ni nombres de revisores.
