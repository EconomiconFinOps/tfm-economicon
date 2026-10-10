# JUP-071: resultado de robustez

Ejecución: `template_mock`. Provisional: `False`.
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

| Caso | Resultado | Juicios pendientes | Eco del prompt |
| --- | --- | ---: | --- |
| JUP-069-002 | fail | 3 | False |
| JUP-069-003 | not_run | 4 | False |
| JUP-069-005 | fail | 6 | False |
| JUP-069-008 | not_run | 5 | False |
| JUP-069-009 | not_run | 4 | False |
| JUP-069-010 | not_run | 4 | False |
| JUP-069-011 | fail | 3 | False |
| JUP-069-012 | not_run | 4 | False |
| JUP-069-016 | fail | 4 | False |
| JUP-069-023 | not_run | 5 | False |
| JUP-069-024 | not_run | 5 | False |
| JUP-069-026 | not_run | 4 | False |
| JUP-069-027 | fail | 4 | False |
| JUP-071-001 | not_run | 6 | False |
| JUP-071-002 | fail | 6 | False |
| JUP-071-003 | fail | 6 | False |
| JUP-071-004 | not_run | 6 | False |
| JUP-071-005 | not_run | 6 | False |
| JUP-071-006 | not_run | 6 | False |
| JUP-071-007 | not_run | 6 | False |
| JUP-071-008 | not_run | 6 | False |
| JUP-071-009 | not_run | 6 | False |
| JUP-071-010 | fail | 6 | False |
| JUP-071-011 | not_run | 6 | False |
| JUP-071-012 | not_run | 5 | False |
| JUP-071-013 | not_run | 6 | False |
| JUP-071-014 | not_run | 6 | False |
| JUP-071-015 | not_run | 6 | False |
| JUP-071-016 | not_run | 6 | False |

Identidad y parejas completas en el JSON asociado. Sin textos de respuestas ni nombres de revisores.
