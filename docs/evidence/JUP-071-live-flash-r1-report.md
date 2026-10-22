# JUP-071: resultado de robustez

Ejecución: `live_unverified` (`JUP-071-864a0d6dc666`). Provisional: `True`.
Robustez generativa: **no acreditada**. El endpoint no acredita qué modelo ejecutó.

Los fallos conocidos se conservan aunque falten juicios. `not_run` incluye semántica pendiente.

| Grupo | Conducta | Total | Pass | Fail | Blocked | Not run |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline | answer | 7 | 1 | 5 | 1 | 0 |
| baseline | clarify | 5 | 2 | 3 | 0 | 0 |
| baseline | abstain | 1 | 1 | 0 | 0 | 0 |
| perturbation | answer | 3 | 0 | 3 | 0 | 0 |
| perturbation | clarify | 12 | 2 | 10 | 0 | 0 |
| perturbation | abstain | 1 | 1 | 0 | 0 | 0 |

Total previsto: 29. pass / total previsto: 24,1 %. pass / (pass + fail): 25,0 %.
El denominador pass / (pass + fail) incluye fallos conocidos con juicios pendientes; no equivale a cobertura de revisión humana completa.
Casos con cobertura reducida: 28. Evaluación completa: no.

## Categorías de perturbación

| Categoría | Total | Pass | Fail | Blocked | Not run | pass / total previsto | pass / (pass + fail) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| tagging | 5 | 0 | 5 | 0 | 0 | 0,0 % | 0,0 % |
| allocation | 4 | 1 | 3 | 0 | 0 | 25,0 % | 25,0 % |
| costs | 3 | 0 | 3 | 0 | 0 | 0,0 % | 0,0 % |
| scope | 3 | 2 | 1 | 0 | 0 | 66,7 % | 66,7 % |
| anomalies | 1 | 0 | 1 | 0 | 0 | 0,0 % | 0,0 % |

## Tipos de perturbación

| Tipo | Total | Pass | Fail | Blocked | Not run |
| --- | ---: | ---: | ---: | ---: | ---: |
| missing_tag_with_sufficient_allocation_rule | 1 | 0 | 1 | 0 | 0 |
| null_tag_value | 1 | 0 | 1 | 0 | 0 |
| empty_and_whitespace_tag_values | 1 | 0 | 1 | 0 | 0 |
| unknown_controlled_tag_value | 1 | 0 | 1 | 0 | 0 |
| conflicting_tags_after_key_normalization | 1 | 0 | 1 | 0 | 0 |
| missing_shared_weights | 1 | 0 | 1 | 0 | 0 |
| ambiguous_shared_weight_units | 1 | 0 | 1 | 0 | 0 |
| missing_eligible_cost_denominator | 1 | 0 | 1 | 0 | 0 |
| confirmed_zero_denominator | 1 | 1 | 0 | 0 | 0 |
| missing_business_volume_denominator | 1 | 0 | 1 | 0 | 0 |
| partial_vs_complete_period | 1 | 0 | 1 | 0 | 0 |
| ambiguous_date_format | 1 | 0 | 1 | 0 | 0 |
| missing_currency_unit | 1 | 0 | 1 | 0 | 0 |
| incompatible_time_units | 1 | 0 | 1 | 0 | 0 |
| empty_result_with_incomplete_ingestion | 1 | 1 | 0 | 0 | 0 |
| unavailable_real_tenant_with_synthetic_decoy | 1 | 1 | 0 | 0 | 0 |

## Casos

| Caso | Resultado | Juicios pendientes | Cobertura reducida | Eco del prompt |
| --- | --- | ---: | --- | --- |
| JUP-069-002 | fail | 0 | True | False |
| JUP-069-003 | pass | 0 | True | False |
| JUP-069-005 | fail | 0 | True | False |
| JUP-069-008 | pass | 0 | True | False |
| JUP-069-009 | fail | 0 | True | False |
| JUP-069-010 | blocked | 0 | False | False |
| JUP-069-011 | fail | 0 | True | False |
| JUP-069-012 | pass | 0 | True | False |
| JUP-069-016 | fail | 0 | True | False |
| JUP-069-023 | pass | 0 | True | False |
| JUP-069-024 | fail | 0 | True | False |
| JUP-069-026 | fail | 0 | True | False |
| JUP-069-027 | fail | 0 | True | False |
| JUP-071-001 | fail | 0 | True | False |
| JUP-071-002 | fail | 0 | True | False |
| JUP-071-003 | fail | 0 | True | False |
| JUP-071-004 | fail | 0 | True | False |
| JUP-071-005 | fail | 0 | True | False |
| JUP-071-006 | fail | 0 | True | False |
| JUP-071-007 | fail | 0 | True | False |
| JUP-071-008 | fail | 0 | True | False |
| JUP-071-009 | pass | 0 | True | False |
| JUP-071-010 | fail | 0 | True | False |
| JUP-071-011 | fail | 0 | True | False |
| JUP-071-012 | fail | 0 | True | False |
| JUP-071-013 | fail | 0 | True | False |
| JUP-071-014 | fail | 0 | True | False |
| JUP-071-015 | pass | 0 | True | False |
| JUP-071-016 | pass | 0 | True | False |

Identidad y parejas completas en el JSON asociado. Sin textos de respuestas ni nombres de revisores.
