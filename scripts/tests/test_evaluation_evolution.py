"""Existing Friday/Sunday evidence, denominator guards and additive loading in disposable PG."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('evolution', ROOT/'tools/evaluation-evolution.py')
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


class Evidence(unittest.TestCase):
    def setUp(self):
        self.report = json.loads((E.DIRECTORY/'observations.json').read_text(encoding='utf8'))

    def test_committed_projections_are_reproducible(self):
        for path, content in E.artifacts().items():
            self.assertEqual(path.read_text(encoding='utf8'), content)
        tool = E.load_tool()
        actual = E.additive_sql(tool.build_dataset([E.MANIFEST]), tool)
        self.assertEqual((E.DIRECTORY/'append.sql').read_text(encoding='utf8'), actual)

    def test_selected_denominators_and_observations_match_audited_evidence(self):
        values = [E.statistics_for(E.common(self.report[p]['cases'], p)) for p in E.RUN_IDS]
        for actual, expected in zip(values, [(132,119,201,35,20.12796,148.796412),(44,41,53,4,12.0195,49.485)]):
            for key, value in zip(('operations','completed','attempts','retried','median_seconds','p95_seconds'), expected):
                self.assertAlmostEqual(actual[key], value)
        self.assertEqual(values[0]['observed_cost_usd'], '0.4435138808')
        self.assertEqual(values[1]['observed_cost_usd'], '0.0727486368')

    def test_full_latest_and_robustness_are_not_cherry_picked(self):
        rows = self.report['sunday']['cases']
        self.assertEqual(E.statistics_for(rows)['completed'], 47)
        self.assertEqual(E.statistics_for(rows)['attempts'], 61)
        for verdict, count in [('PASS',39),('PARTIAL',7),('FAIL',4)]:
            self.assertEqual(sum(r['functional_verdict']==verdict for r in rows), count)
        for p in E.RUN_IDS:
            subset = [r for r in E.common(self.report[p]['cases'],p) if r['case_id'].startswith('JUP-071-')]
            stats = E.statistics_for(subset)
            self.assertEqual(stats['completed']/stats['operations'], .875)

    def test_missing_duplicate_or_invalid_measurements_are_rejected(self):
        for mutation in ('missing','duplicate','nan','negative','state'):
            d = copy.deepcopy(self.report)
            rows = d['sunday']['cases']
            if mutation=='missing': rows.pop()
            elif mutation=='duplicate': rows[1]=copy.deepcopy(rows[0])
            elif mutation=='nan': rows[0]['seconds']=float('nan')
            elif mutation=='negative': rows[0]['cost_usd']='-1'
            else: rows[0]['state']='running'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                E.validate_observations(d)

    def test_no_raw_conversations_or_operational_identifiers_are_published(self):
        forbidden = {'question','answer','prompt','conversation_id','operation_id','request_id','tenant','authorization','api_key','token','password'}
        def walk(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value))
                for v in value.values(): walk(v)
            elif isinstance(value,list):
                for v in value: walk(v)
        walk(self.report)

    def test_identity_unknowns_and_incompatible_cohorts_remain_explicit(self):
        tool = E.load_tool()
        dataset = tool.build_dataset([E.MANIFEST])
        runs = [x['run'] for x in dataset['runs']]
        self.assertEqual(len(runs),2)
        self.assertNotEqual(runs[0]['comparability_key'],runs[1]['comparability_key'])
        for r in runs:
            self.assertIsNone(r['generation_model'])
            self.assertFalse(r['is_real'])
            self.assertFalse(r['milestone'])
        self.assertIsNone(runs[0]['commit'])
        self.assertEqual(runs[1]['commit'],'390721f92d60d29358de62e9cebf99ee028190a2')
        friday = dataset['runs'][0]['results']; sunday = dataset['runs'][1]['results']
        self.assertFalse(any(r['grp']=='evolution_agent_functional' for r in friday))
        self.assertTrue(all(r['value'] is None for r in sunday if r['judgment']=='human'))
        self.assertNotEqual({r['metric_id'] for r in friday if r['grp']=='evolution_cost'},
                            {r['metric_id'] for r in sunday if r['grp']=='evolution_cost'})


class AdditivePostgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import evaluation_pg_helper
        cls.server = evaluation_pg_helper.PostgresServer()
        cls.tool = E.load_tool()
        cls.dataset = cls.tool.build_dataset([ROOT/'docs/validation/evaluation-runs.json'])
        cls.sql = (E.DIRECTORY/'append.sql').read_text(encoding='utf8')
        cls.dashboard = json.loads((ROOT/'apps/monitoring/grafana/dashboards/assistant-evidence.json').read_text(encoding='utf8'))

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self):
        self.server.load_dataset(self.dataset,self.tool)

    def execute(self,sql):
        r = self.server.psql(sql)
        self.assertEqual(r.returncode,0,r.stderr)
        return r.stdout

    def digest(self,table,predicate='true'):
        return self.server.scalar(f"SELECT md5(string_agg(to_jsonb(t)::text,',' ORDER BY to_jsonb(t)::text)) FROM evaluation.{table} t WHERE {predicate}")

    def panel(self,pid):
        p = next(p for p in self.dashboard['panels'] if p['id']==pid)
        return json.loads(self.server.scalar("SELECT coalesce(jsonb_agg(to_jsonb(q)),'[]'::jsonb) FROM ("+p['targets'][0]['rawSql']+") q"))

    def test_addition_and_repetition_preserve_every_historical_cell_including_extra_run(self):
        self.execute("INSERT INTO evaluation.runs SELECT (jsonb_populate_record(NULL::evaluation.runs,to_jsonb(r)||'{\"run_id\":\"extra-runtime\"}'::jsonb)).* FROM evaluation.runs r LIMIT 1;")
        self.execute("DELETE FROM evaluation.runs WHERE run_id LIKE 'jup133-evolution-%';")
        before = {t:self.digest(t) for t in ('runs','results')}
        self.execute(self.sql)
        for t in before:
            self.assertEqual(before[t],self.digest(t,"run_id NOT LIKE 'jup133-evolution-%'"))
        full = {t:self.digest(t) for t in before}
        self.execute(self.sql)
        self.assertEqual(full,{t:self.digest(t) for t in before})
        self.assertEqual(self.server.scalar('SELECT count(*) FROM evaluation.runs'),'21')

    def test_conflicting_metadata_aborts_whole_transaction(self):
        self.execute("DELETE FROM evaluation.runs WHERE run_id='jup133-evolution-sunday-20261025'; UPDATE evaluation.runs SET commit_sha='conflict' WHERE run_id='jup133-evolution-friday-20261023';")
        before = {t:self.digest(t) for t in ('runs','results')}
        r = self.server.psql(self.sql)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('identity/content conflict',r.stderr)
        self.assertEqual(before,{t:self.digest(t) for t in before})

    def test_conflicting_measurement_not_hidden_by_unchanged_report_hash(self):
        self.execute("UPDATE evaluation.results SET value=999 WHERE run_id='jup133-evolution-friday-20261023' AND metric_id='completed' AND behavior='common44';")
        before = self.digest('results')
        self.assertNotEqual(self.server.psql(self.sql).returncode,0)
        self.assertEqual(before,self.digest('results'))

    def test_missing_or_extra_existing_row_aborts(self):
        for mode in ('missing','extra'):
            self.server.load_dataset(self.dataset,self.tool)
            if mode=='missing':
                self.execute("DELETE FROM evaluation.results WHERE run_id='jup133-evolution-friday-20261023' AND metric_id='completed' AND behavior='common44';")
            else:
                self.execute("INSERT INTO evaluation.results SELECT (jsonb_populate_record(NULL::evaluation.results,to_jsonb(r)||'{\"metric_id\":\"unexpected\"}'::jsonb)).* FROM evaluation.results r WHERE run_id='jup133-evolution-friday-20261023' LIMIT 1;")
            before = self.digest('results')
            with self.subTest(mode=mode):
                self.assertNotEqual(self.server.psql(self.sql).returncode,0)
                self.assertEqual(before,self.digest('results'))

    def test_dashboard_queries_match_observations_and_do_not_equate_quality_with_completion(self):
        rows = self.panel(8401)
        self.assertEqual(len(rows),6)
        common = [r for r in rows if r['Casos distintos']=='44 casos comunes']
        self.assertEqual([r['Operaciones'] for r in common],[132,44])
        self.assertEqual([r['Completadas (%)'] for r in common],[90.2,93.2])
        times = self.panel(8402)
        self.assertEqual(len(times),6)
        current = self.panel(8403)[0]
        self.assertEqual([current[k] for k in ('Operaciones','Completadas','Conformes IA','Parciales IA','Fallos IA')],[50,47,39,7,4])
        self.assertAlmostEqual(current['USD observados incompletos'],.0808892056)

    def test_absent_campaigns_are_not_fabricated_as_zero(self):
        self.execute("DELETE FROM evaluation.runs WHERE run_id='jup133-evolution-sunday-20261025';")
        self.assertEqual(self.panel(8403),[])
        self.assertEqual(len(self.panel(8401)),3)
        self.execute("DELETE FROM evaluation.runs WHERE run_id='jup133-evolution-friday-20261023';")
        self.assertEqual(self.panel(8401),[])
        self.assertEqual(self.panel(8402),[])


if __name__=='__main__':
    unittest.main()
