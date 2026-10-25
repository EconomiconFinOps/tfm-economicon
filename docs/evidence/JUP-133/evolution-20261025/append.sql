\set ON_ERROR_STOP on
BEGIN;
SET LOCAL lock_timeout = '15s';
SET LOCAL standard_conforming_strings = on;
LOCK TABLE evaluation.runs, evaluation.results IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE evolution_runs (LIKE evaluation.runs INCLUDING ALL) ON COMMIT DROP;
CREATE TEMP TABLE evolution_results (LIKE evaluation.results INCLUDING ALL) ON COMMIT DROP;
INSERT INTO evolution_runs (run_id, source, run_at, commit_sha, suite, suite_version, suite_sha256, corpus_sha256, embedding_provider, embedding_alias, retrieval, generation_model, prompt_sha256, synthetic, generation_model_id, generation_provider, generation_quantization, gateway_config_sha256, is_real, non_real_reasons, comparability_key, format, milestone, report_path, report_sha256) VALUES
  ('jup133-evolution-friday-20261023', 'JUP-133', '2026-10-23T16:32:09.606881+00:00'::timestamptz, NULL, 'descriptive-friday-sunday', 'polling-v1', '94e94e18ce28a80105b6343e962cf37dada4ba6d6a9a0f8c3ce88a77ad9f9fa5', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 'openrouter/deepseek/deepseek-v4.1-flash', 'deepinfra', 'fp8', NULL, FALSE, ARRAY['sin_modelo_verificado']::text[], '496b78bcaa5c03aa2209a852feaf2d3d68b128782806f08ac05c903ab33190f8', 'rows-v1', FALSE, 'docs/evidence/JUP-133/evolution-20261025/friday.rows.json', '34a77731a9156d62304cd22569a8a6ee94123b84fcada9085cd5cb1e762e1261'),
  ('jup133-evolution-sunday-20261025', 'JUP-133', '2026-10-25T16:11:40.224616+00:00'::timestamptz, '390721f92d60d29358de62e9cebf99ee028190a2', 'descriptive-friday-sunday', 'client-capture-v1', '94e94e18ce28a80105b6343e962cf37dada4ba6d6a9a0f8c3ce88a77ad9f9fa5', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 'openrouter/deepseek/deepseek-v4.1-flash', 'deepinfra', 'fp8', NULL, FALSE, ARRAY['sin_modelo_verificado']::text[], 'f218e10432226031097c8e6c0bb0cb495d9ad0a66eabbe5c50aaebf8646d9870', 'rows-v1', FALSE, 'docs/evidence/JUP-133/evolution-20261025/sunday.rows.json', '29d32dc52d08b3f747bd01e8e2a4d23f26d293b06f3af582ed60145911c7bebe');

INSERT INTO evolution_results (run_id, measure_type, grp, metric_id, behavior, status, case_count, value, unit, numerator, denominator, ci_low, ci_high, judgment, selected) VALUES
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'operations', 'full', 'measured', NULL, 171, 'recuento', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed', 'full', 'measured', NULL, 158, 'recuento', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'failed', 'full', 'measured', NULL, 13, 'recuento', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'attempts', 'full', 'measured', NULL, 248, 'recuento', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried', 'full', 'measured', NULL, 42, 'recuento', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed_rate', 'full', 'measured', NULL, 0.9239766081871345, 'tasa', 158, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried_rate', 'full', 'measured', NULL, 0.24561403508771928, 'tasa', 42, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'median_seconds', 'full', 'measured', NULL, 19.777134999999998, 's', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'p95_seconds', 'full', 'measured', NULL, 148.45136300000001, 's', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'max_seconds', 'full', 'measured', NULL, 314.65318, 's', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_cost', 'gateway_settled_with_embeddings', 'full', 'measured', NULL, 0.5291594448, 'usd', NULL, 171, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'operations', 'common44', 'measured', NULL, 132, 'recuento', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed', 'common44', 'measured', NULL, 119, 'recuento', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'failed', 'common44', 'measured', NULL, 13, 'recuento', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'attempts', 'common44', 'measured', NULL, 201, 'recuento', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried', 'common44', 'measured', NULL, 35, 'recuento', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed_rate', 'common44', 'measured', NULL, 0.9015151515151515, 'tasa', 119, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried_rate', 'common44', 'measured', NULL, 0.26515151515151514, 'tasa', 35, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'median_seconds', 'common44', 'measured', NULL, 20.127959999999998, 's', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'p95_seconds', 'common44', 'measured', NULL, 148.796412, 's', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'max_seconds', 'common44', 'measured', NULL, 314.65318, 's', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_cost', 'gateway_settled_with_embeddings', 'common44', 'measured', NULL, 0.4435138808, 'usd', NULL, 132, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'operations', 'general28', 'measured', NULL, 84, 'recuento', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed', 'general28', 'measured', NULL, 77, 'recuento', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'failed', 'general28', 'measured', NULL, 7, 'recuento', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'attempts', 'general28', 'measured', NULL, 122, 'recuento', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried', 'general28', 'measured', NULL, 17, 'recuento', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed_rate', 'general28', 'measured', NULL, 0.9166666666666666, 'tasa', 77, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried_rate', 'general28', 'measured', NULL, 0.20238095238095238, 'tasa', 17, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'median_seconds', 'general28', 'measured', NULL, 19.2179035, 's', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'p95_seconds', 'general28', 'measured', NULL, 148.45136300000001, 's', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'max_seconds', 'general28', 'measured', NULL, 186.755403, 's', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_cost', 'gateway_settled_with_embeddings', 'general28', 'measured', NULL, 0.267801508, 'usd', NULL, 84, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'operations', 'robust16', 'measured', NULL, 48, 'recuento', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed', 'robust16', 'measured', NULL, 42, 'recuento', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'failed', 'robust16', 'measured', NULL, 6, 'recuento', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'attempts', 'robust16', 'measured', NULL, 79, 'recuento', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried', 'robust16', 'measured', NULL, 18, 'recuento', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'completed_rate', 'robust16', 'measured', NULL, 0.875, 'tasa', 42, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_operations', 'retried_rate', 'robust16', 'measured', NULL, 0.375, 'tasa', 18, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'median_seconds', 'robust16', 'measured', NULL, 22.805484, 's', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'p95_seconds', 'robust16', 'measured', NULL, 150.92420199999998, 's', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_times', 'max_seconds', 'robust16', 'measured', NULL, 314.65318, 's', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_cost', 'gateway_settled_with_embeddings', 'robust16', 'measured', NULL, 0.1757123728, 'usd', NULL, 48, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-friday-20261023', 'A', 'evolution_human', 'acceptance', 'full', 'not_measured', NULL, NULL, 'tasa', NULL, NULL, NULL, NULL, 'human', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'operations', 'full', 'measured', NULL, 50, 'recuento', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed', 'full', 'measured', NULL, 47, 'recuento', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'failed', 'full', 'measured', NULL, 3, 'recuento', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'attempts', 'full', 'measured', NULL, 61, 'recuento', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried', 'full', 'measured', NULL, 5, 'recuento', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed_rate', 'full', 'measured', NULL, 0.94, 'tasa', 47, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried_rate', 'full', 'measured', NULL, 0.1, 'tasa', 5, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'median_seconds', 'full', 'measured', NULL, 12.8565, 's', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'p95_seconds', 'full', 'measured', NULL, 60.719, 's', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'max_seconds', 'full', 'measured', NULL, 65.892, 's', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_cost', 'chat_observed_incomplete', 'full', 'measured', NULL, 0.0808892056, 'usd', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'pass', 'full', 'measured', NULL, 39, 'casos', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'partial', 'full', 'measured', NULL, 7, 'casos', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'fail', 'full', 'measured', NULL, 4, 'casos', NULL, 50, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'operations', 'common44', 'measured', NULL, 44, 'recuento', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed', 'common44', 'measured', NULL, 41, 'recuento', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'failed', 'common44', 'measured', NULL, 3, 'recuento', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'attempts', 'common44', 'measured', NULL, 53, 'recuento', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried', 'common44', 'measured', NULL, 4, 'recuento', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed_rate', 'common44', 'measured', NULL, 0.9318181818181818, 'tasa', 41, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried_rate', 'common44', 'measured', NULL, 0.09090909090909091, 'tasa', 4, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'median_seconds', 'common44', 'measured', NULL, 12.0195, 's', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'p95_seconds', 'common44', 'measured', NULL, 49.485, 's', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'max_seconds', 'common44', 'measured', NULL, 65.892, 's', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_cost', 'chat_observed_incomplete', 'common44', 'measured', NULL, 0.0727486368, 'usd', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'pass', 'common44', 'measured', NULL, 36, 'casos', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'partial', 'common44', 'measured', NULL, 5, 'casos', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'fail', 'common44', 'measured', NULL, 3, 'casos', NULL, 44, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'operations', 'general28', 'measured', NULL, 28, 'recuento', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed', 'general28', 'measured', NULL, 27, 'recuento', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'failed', 'general28', 'measured', NULL, 1, 'recuento', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'attempts', 'general28', 'measured', NULL, 32, 'recuento', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried', 'general28', 'measured', NULL, 2, 'recuento', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed_rate', 'general28', 'measured', NULL, 0.9642857142857143, 'tasa', 27, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried_rate', 'general28', 'measured', NULL, 0.07142857142857142, 'tasa', 2, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'median_seconds', 'general28', 'measured', NULL, 10.7785, 's', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'p95_seconds', 'general28', 'measured', NULL, 27.731, 's', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'max_seconds', 'general28', 'measured', NULL, 60.719, 's', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_cost', 'chat_observed_incomplete', 'general28', 'measured', NULL, 0.0433961696, 'usd', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'pass', 'general28', 'measured', NULL, 26, 'casos', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'partial', 'general28', 'measured', NULL, 1, 'casos', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'fail', 'general28', 'measured', NULL, 1, 'casos', NULL, 28, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'operations', 'robust16', 'measured', NULL, 16, 'recuento', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed', 'robust16', 'measured', NULL, 14, 'recuento', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'failed', 'robust16', 'measured', NULL, 2, 'recuento', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'attempts', 'robust16', 'measured', NULL, 21, 'recuento', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried', 'robust16', 'measured', NULL, 2, 'recuento', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed_rate', 'robust16', 'measured', NULL, 0.875, 'tasa', 14, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried_rate', 'robust16', 'measured', NULL, 0.125, 'tasa', 2, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'median_seconds', 'robust16', 'measured', NULL, 16.6565, 's', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'p95_seconds', 'robust16', 'measured', NULL, 65.892, 's', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'max_seconds', 'robust16', 'measured', NULL, 65.892, 's', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_cost', 'chat_observed_incomplete', 'robust16', 'measured', NULL, 0.0293524672, 'usd', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'pass', 'robust16', 'measured', NULL, 10, 'casos', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'partial', 'robust16', 'measured', NULL, 4, 'casos', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'fail', 'robust16', 'measured', NULL, 2, 'casos', NULL, 16, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'operations', 'reported4', 'measured', NULL, 4, 'recuento', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed', 'reported4', 'measured', NULL, 4, 'recuento', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'failed', 'reported4', 'measured', NULL, 0, 'recuento', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'attempts', 'reported4', 'measured', NULL, 6, 'recuento', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried', 'reported4', 'measured', NULL, 1, 'recuento', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed_rate', 'reported4', 'measured', NULL, 1.0, 'tasa', 4, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried_rate', 'reported4', 'measured', NULL, 0.25, 'tasa', 1, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'median_seconds', 'reported4', 'measured', NULL, 17.778, 's', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'p95_seconds', 'reported4', 'measured', NULL, 61.766, 's', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'max_seconds', 'reported4', 'measured', NULL, 61.766, 's', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_cost', 'chat_observed_incomplete', 'reported4', 'measured', NULL, 0.005146764, 'usd', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'pass', 'reported4', 'measured', NULL, 3, 'casos', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'partial', 'reported4', 'measured', NULL, 1, 'casos', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'fail', 'reported4', 'measured', NULL, 0, 'casos', NULL, 4, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'operations', 'screen2', 'measured', NULL, 2, 'recuento', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed', 'screen2', 'measured', NULL, 2, 'recuento', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'failed', 'screen2', 'measured', NULL, 0, 'recuento', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'attempts', 'screen2', 'measured', NULL, 2, 'recuento', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried', 'screen2', 'measured', NULL, 0, 'recuento', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'completed_rate', 'screen2', 'measured', NULL, 1.0, 'tasa', 2, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_operations', 'retried_rate', 'screen2', 'measured', NULL, 0.0, 'tasa', 0, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'median_seconds', 'screen2', 'measured', NULL, 23.671, 's', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'p95_seconds', 'screen2', 'measured', NULL, 27.541, 's', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_times', 'max_seconds', 'screen2', 'measured', NULL, 27.541, 's', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_cost', 'chat_observed_incomplete', 'screen2', 'measured', NULL, 0.0029938048, 'usd', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'pass', 'screen2', 'measured', NULL, 0, 'casos', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'partial', 'screen2', 'measured', NULL, 1, 'casos', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_agent_functional', 'fail', 'screen2', 'measured', NULL, 1, 'casos', NULL, 2, NULL, NULL, 'automatic', FALSE),
  ('jup133-evolution-sunday-20261025', 'A', 'evolution_human', 'acceptance', 'full', 'not_measured', NULL, NULL, 'tasa', NULL, NULL, NULL, NULL, 'human', FALSE);
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM evolution_runs n JOIN evaluation.runs o USING (run_id)
    WHERE to_jsonb(n) IS DISTINCT FROM to_jsonb(o)
  ) OR EXISTS (
    (SELECT to_jsonb(n) FROM evolution_results n JOIN evaluation.runs o USING(run_id)
     EXCEPT ALL
     SELECT to_jsonb(o) FROM evaluation.results o JOIN evolution_runs n USING(run_id))
    UNION ALL
    (SELECT to_jsonb(o) FROM evaluation.results o JOIN evolution_runs n USING(run_id)
     EXCEPT ALL
     SELECT to_jsonb(n) FROM evolution_results n JOIN evaluation.runs o USING(run_id))
  ) THEN
    RAISE EXCEPTION 'JUP-133 evolution identity/content conflict; reconcile before loading';
  END IF;
END $$;
CREATE TEMP TABLE evolution_missing ON COMMIT DROP AS
SELECT n.run_id FROM evolution_runs n WHERE NOT EXISTS
(SELECT 1 FROM evaluation.runs o WHERE o.run_id=n.run_id);
INSERT INTO evaluation.runs SELECT n.* FROM evolution_runs n JOIN evolution_missing m USING(run_id);
INSERT INTO evaluation.results SELECT n.* FROM evolution_results n JOIN evolution_missing m USING(run_id);
COMMIT;
