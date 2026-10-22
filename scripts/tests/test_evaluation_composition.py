"""Narrative composition: nulls, one-campaign scope and compatible comparisons.

Uses the existing disposable PostgreSQL helper by default. An explicitly supplied
EVALUATION_COMPOSITION_PGHOST/PGPORT/PGDATABASE/PGUSER and PSQL path selects an
already prepared, disposable database; no dataset is loaded into that database.
Every scenario is a transaction ending in ROLLBACK. Native passwords use the
standard PGPASSWORD environment variable and are never logged.
"""
from __future__ import annotations
import json,os,re,secrets,subprocess,unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
DASHBOARD=ROOT/'apps/monitoring/grafana/dashboards/assistant-evidence.json'

def panels(items):
    for p in items:
        yield p
        yield from panels(p.get('panels',[]))

def literal(value):
    return "'"+str(value).replace("'","''")+"'"

class CompositionStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard=json.loads(DASHBOARD.read_text(encoding='utf8'))
        cls.by_id={p['id']:p for p in panels(cls.dashboard['panels'])}

    def test_native_graphs_and_separate_sources(self):
        d=self.dashboard
        self.assertEqual(d['uid'],'economicon-assistant-evidence')
        self.assertEqual(d['timezone'],'utc')
        self.assertFalse(d['editable'])
        self.assertEqual(self.by_id[106]['options']['pieType'],'donut')
        self.assertEqual(self.by_id[110]['type'],'table')
        self.assertEqual(self.by_id[107]['options']['stacking'],'none')
        self.assertEqual(self.by_id[114]['type'],'xychart')
        self.assertEqual(len(self.by_id[114]['targets']),2)
        self.assertEqual(self.by_id[114]['fieldConfig']['defaults']['custom']['show'],'points')
        for p in self.by_id.values():
            if p['type'] in ('text','row'):continue
            self.assertIn(p['datasource']['uid'],('evaluation-postgres','prometheus'))
            self.assertTrue(all(t.get('datasource',p['datasource'])==p['datasource'] for t in p.get('targets',[])))

    def test_folded_secondary_and_unique_identity(self):
        all_panels=list(panels(self.dashboard['panels']))
        self.assertEqual(len(all_panels),len(self.by_id))
        for i in (320,117,118):self.assertTrue(self.by_id[i]['collapsed'])
        for p in all_panels:
            g=p['gridPos'];self.assertGreater(g['h'],0);self.assertGreater(g['w'],0)
            self.assertLessEqual(g['x']+g['w'],24)
        # Existing consumers and audit surfaces retain their stable UIDs.
        old=json.loads((DASHBOARD.parent/'assistant-evaluation.json').read_text(encoding='utf8'))
        technical=json.loads((DASHBOARD.parent/'technical-metrics.json').read_text(encoding='utf8'))
        self.assertEqual(old['uid'],'economicon-assistant-evaluation')
        self.assertEqual(technical['uid'],'economicon-technical-metrics')

    def test_operational_health_does_not_claim_a_permanently_missing_datasource(self):
        self.assertNotIn('preview',self.by_id[117]['title'])
        self.assertNotIn('Sin fuente Prometheus suministrada',self.by_id[901]['options']['content'])
        self.assertIn('Sin series disponibles',self.by_id[901]['options']['content'])
        for i in (902,903,904):
            self.assertEqual(self.by_id[i]['datasource']['uid'],'prometheus')
            self.assertEqual(self.by_id[i]['timeFrom'],'1h')

    def test_public_titles_text_and_help_have_no_internal_references(self):
        bad=re.compile(r'JUP[- ]?\d|PR\d|bc94|c213|develop|T-800|\bR[123]\b|\bAgente\b|\bSHA\b',re.I)
        for p in list(self.by_id.values())+[self.dashboard]:
            for k in ('title','description'):
                self.assertNotRegex(p.get(k,''),bad)
            self.assertNotRegex(p.get('options',{}).get('content',''),bad)
            self.assertNotRegex(p.get('fieldConfig',{}).get('defaults',{}).get('noValue',''),bad)
        for v in self.dashboard['templating']['list']:
            self.assertNotRegex(v.get('current',{}).get('text',''),bad)
        self.assertFalse(self.dashboard.get('links'))

    def test_real_variable_values_are_sql_escaped_and_defaults_not_frozen(self):
        variables=self.dashboard['templating']['list']
        self.assertEqual([v['name'] for v in variables],['campaign','reference','model_availability'])
        self.assertEqual(variables[2]['hide'],2)
        self.assertTrue(variables[2]['skipUrlSync'])
        self.assertFalse(variables[0]['current'])
        self.assertEqual(variables[1]['current']['value'],'__none__')
        self.assertIn('__value',variables[0]['query'])
        for p in self.by_id.values():
            for t in p.get('targets',[]):
                sql=t.get('rawSql','')
                self.assertNotIn("'${campaign}'",sql)
                self.assertNotIn(':raw}',sql)
                if '${campaign' in sql:self.assertIn('${campaign:sqlstring}',sql)

    def test_historical_aggregates_are_one_report_and_missing_values_not_zero(self):
        for i in (110,322,323,324,325):
            q=self.by_id[i]['targets'][0]['rawSql']
            self.assertRegex(q.split(" FROM ",1)[1],r"WHERE r\.run_id='[^']+' AND ")
        for p in self.by_id.values():
            if p.get('datasource',{}).get('uid')!='evaluation-postgres':continue
            self.assertRegex(self.by_id[p['id']]['fieldConfig']['defaults']['noValue'],r'^(No medido|Sin datos)(?:$|:)')
            for t in p.get('targets',[]):
                self.assertNotRegex(t.get('rawSql',''),r'(?i)coalesce\([^)]*,\s*0\s*\)')

class CompositionSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import evaluation_pg_helper
        cls.tool=evaluation_pg_helper.load_tool()
        cls.dashboard=json.loads(DASHBOARD.read_text(encoding='utf8'))
        cls.by_id={p['id']:p for p in panels(cls.dashboard['panels'])}
        cls.server=None
        if os.environ.get('EVALUATION_COMPOSITION_PGHOST'):
            required=['EVALUATION_COMPOSITION_PSQL','EVALUATION_COMPOSITION_PGPORT','EVALUATION_COMPOSITION_PGDATABASE','EVALUATION_COMPOSITION_PGUSER']
            for key in required:
                if not os.environ.get(key):raise RuntimeError('Missing explicit disposable database setting: '+key)
        else:
            cls.server=evaluation_pg_helper.PostgresServer()
            cls.addClassCleanup(cls.server.stop)
            cls.server.load_dataset(cls.tool.build_dataset([cls.tool.DEFAULT_MANIFEST]),cls.tool)
            result=cls.server.psql(stdin=cls.tool.build_role_sql(secrets.token_urlsafe(18)))
            if result.returncode:raise RuntimeError(result.stderr)

    def psql(self,sql):
        if self.server:return self.server.psql(stdin=sql)
        e=os.environ
        return subprocess.run([e['EVALUATION_COMPOSITION_PSQL'],'-h',e['EVALUATION_COMPOSITION_PGHOST'],'-p',e['EVALUATION_COMPOSITION_PGPORT'],'-U',e['EVALUATION_COMPOSITION_PGUSER'],'-d',e['EVALUATION_COMPOSITION_PGDATABASE'],'-XqAt','-v','ON_ERROR_STOP=1'],input=sql,capture_output=True,text=True,encoding='utf8')

    def query(self,sql,setup='',campaign='composition-current',reference='composition-reference'):
        sql=sql.replace('${campaign:sqlstring}',literal(campaign)).replace('${reference:sqlstring}',literal(reference))
        result=self.psql('BEGIN;\n'+setup+'\nSET LOCAL ROLE grafana_evaluation_reader;\nSELECT COALESCE(jsonb_agg(to_jsonb(q)),\'[]\'::jsonb) FROM ('+sql+') q;\nROLLBACK;')
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(next(line for line in reversed(result.stdout.splitlines()) if line.startswith('[')))

    def panel(self,i,**kwargs):
        return self.query(self.by_id[i]['targets'][0]['rawSql'],**kwargs)

    def fixture(self,*,key='same-context',date='2026-10-20T12:00:00Z',source='JUP-070'):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        s=insertar_ejecucion('composition-current','JUP-070','2026-10-21T12:00:00Z',clave='same-context')
        s+=insertar_ejecucion('composition-reference',source,date,clave=key)
        for run,value in [('composition-current',0.8),('composition-reference',0.7)]:
            s+=insertar_resultado(run,'relevance','REL-1',valor=value,numerador=round(value*20),denominador=20)
        return s

    def test_all_sql_queries_execute_as_reader_on_manifest_projection(self):
        dataset=self.tool.build_dataset([self.tool.DEFAULT_MANIFEST])
        campaigns=[x['run']['run_id'] for x in dataset['runs'] if x['run']['source'] in ('JUP-070','JUP-071')]
        selected=campaigns[-1] if campaigns else '__none__'
        for p in self.by_id.values():
            if p.get('datasource',{}).get('uid')!='evaluation-postgres':continue
            for t in p.get('targets',[]):
                with self.subTest(panel=p['id']):self.query(t['rawSql'],campaign=selected,reference='__none__')
        for v in self.dashboard['templating']['list']:self.query(v['query'],campaign=selected,reference='__none__')

    def other_historical_report(self, run, other, source, value):
        from evaluation_readability_support import insertar_ejecucion
        return insertar_ejecucion(other,source,'2026-10-22T12:00:00Z')+f"""
INSERT INTO evaluation.results
 (run_id,measure_type,grp,metric_id,behavior,status,case_count,value,unit,numerator,denominator,ci_low,ci_high,judgment,selected)
SELECT {literal(other)},measure_type,grp,metric_id,behavior,status,case_count,
 CASE WHEN status='measured' THEN {value} ELSE value END,unit,numerator,denominator,ci_low,ci_high,judgment,selected
FROM evaluation.results WHERE run_id={literal(run)};
"""

    def test_calibration_report_isolated_from_other_runs_and_absence(self):
        run='jup-022-20261015T092121Z-1d88198f'
        expected=self.panel(110)
        self.assertTrue(expected)
        setup=self.other_historical_report(run,'composition-other-calibration','JUP-022',1)
        self.assertEqual(self.panel(110,setup=setup),expected)
        setup+=f"DELETE FROM evaluation.results WHERE run_id={literal(run)};"
        self.assertEqual(self.panel(110,setup=setup),[])

    def test_cost_window_isolated_from_other_runs_and_absence(self):
        run='jup130-ai-cost-2026-10-09-to-2026-10-21'
        expected=self.panel(322)
        self.assertIsNotNone(expected[0]['Estimado'])
        self.assertIsNotNone(expected[0]['Facturado'])
        setup=self.other_historical_report(run,'composition-other-cost','JUP-130-ai-cost',999)
        self.assertEqual(self.panel(322,setup=setup),expected)
        setup+=f"DELETE FROM evaluation.results WHERE run_id={literal(run)};"
        row=self.panel(322,setup=setup)[0]
        self.assertIsNone(row['Estimado'])
        self.assertIsNone(row['Facturado'])

    def test_missing_models_preserve_null_coordinates_without_zero(self):
        setup="DELETE FROM evaluation.results WHERE run_id='jup-063-undated-1df92bdb';"
        for target in self.by_id[114]['targets']:
            with self.subTest(target=target['refId']):
                rows=self.query(target['rawSql'],setup=setup)
                self.assertEqual(len(rows),1)
                self.assertTrue(all(value is None for value in rows[0].values()))

    def test_model_availability_labels_absent_partial_and_two_observations(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        query=next(v['query'] for v in self.dashboard['templating']['list'] if v['name']=='model_availability')
        run='jup-063-undated-1df92bdb'
        setup=f"DELETE FROM evaluation.runs WHERE run_id={literal(run)};"
        self.assertEqual(self.query(query,setup=setup),[{'__text':'Sin datos','__value':'Sin datos'}])
        setup+=insertar_ejecucion(run,'JUP-063','2026-10-16T12:00:00Z')
        setup+=f"UPDATE evaluation.runs SET format='jup-063-paired-v1' WHERE run_id={literal(run)};"
        for behavior,label in [('DeepSeekV4.1Flash','Datos parciales'),('GLM5.2','Dos observaciones')]:
            for metric in ('reported_phase_cost_usd','generation_seconds_p95'):
                setup+=insertar_resultado(run,'paired_local_provisional',metric,behavior,valor=1)
            self.assertEqual(self.query(query,setup=setup),[{'__text':label,'__value':label}])

    def test_missing_campaign_is_null_not_zero(self):
        for i in (102,103,104,105,306,307,308,309):
            with self.subTest(panel=i):self.assertEqual(list(self.panel(i,campaign='not-loaded')[0].values()),[None])
        self.assertTrue(all(v is None for v in self.panel(106,campaign='not-loaded')[0].values()))
        self.assertEqual(self.panel(304,campaign='not-loaded'),[])
        self.assertEqual(self.panel(311,campaign='not-loaded')[0]['Estado'],'Sin datos')

    def test_quoted_variable_cannot_select_other_campaigns(self):
        result=self.panel(102,campaign="x' OR TRUE --")
        self.assertIsNone(result[0]['casos'])

    def test_single_campaign_counts_and_measured_zero_remain_distinct(self):
        from evaluation_readability_support import insertar_resultado,insertar_ejecucion
        s=self.fixture()+insertar_ejecucion('composition-other','JUP-070','2026-10-19T12:00:00Z')
        for state,count in [('pass',7),('fail',17),('blocked',5),('not_run',0)]:
            s+=insertar_resultado('composition-current','cases','cases',estado=state,unidad='casos',denominador=29,recuento=count,juicio=None)
        s+=insertar_resultado('composition-other','cases','cases',estado='pass',unidad='casos',denominador=99,recuento=99,juicio=None)
        self.assertEqual(self.panel(102,setup=s)[0]['casos'],'7 / 29')
        self.assertEqual(self.panel(103,setup=s)[0]['casos'],'17 / 29')
        self.assertEqual(self.panel(104,setup=s)[0]['casos'],'5 / 29')
        self.assertEqual(self.panel(105,setup=s)[0]['casos'],'24 / 29')
        self.assertEqual(self.panel(106,setup=s),[{'Favorables':7,'Fallidos':17,'Sin evaluar':5}])
        s0=insertar_ejecucion('composition-zero','JUP-070','2026-10-21T12:00:00Z')+insertar_resultado('composition-zero','cases','cases',estado='pass',unidad='casos',denominador=1,recuento=0,juicio=None)
        self.assertEqual(self.panel(102,setup=s0,campaign='composition-zero')[0]['casos'],'0 / 1')

    def test_compatible_pair_shows_existing_values_without_composite_score(self):
        setup=self.fixture()
        self.assertEqual(self.panel(311,setup=setup)[0]['Estado'],'Comparación disponible')
        rows=self.panel(330,setup=setup)
        self.assertEqual(len(rows),1)
        self.assertAlmostEqual(rows[0]['Actual'],0.8)
        self.assertAlmostEqual(rows[0]['Referencia'],0.7)
        self.assertEqual(rows[0]['Cambio observado'],'Aumenta')
        self.assertEqual(rows[0]['Unidad'],'tasa')
        self.assertEqual(rows[0]['n actual'],20)
        self.assertEqual(rows[0]['n referencia'],20)

    def test_incompatible_pair_has_no_delta_rows(self):
        for args in ({'key':'other-corpus'},{'source':'JUP-071'}):
            with self.subTest(args=args):
                self.assertEqual(self.panel(311,setup=self.fixture(**args))[0]['Estado'],'No comparable')
                self.assertEqual(self.panel(330,setup=self.fixture(**args)),[])

    def test_absent_same_or_later_reference_does_not_claim_improvement(self):
        setup=self.fixture()
        self.assertEqual(self.panel(311,setup=setup,reference='__none__')[0]['Estado'],'Sin referencia')
        self.assertEqual(self.panel(311,setup=setup,reference='composition-current')[0]['Estado'],'Misma ejecución')
        self.assertEqual(self.panel(311,setup=self.fixture(date='2026-10-22T12:00:00Z'))[0]['Estado'],'Sin orden temporal')

    def test_unchanged_and_absent_metrics_are_not_improvements(self):
        setup=self.fixture()+"UPDATE evaluation.results SET value=0.7 WHERE run_id='composition-current';"
        self.assertEqual(self.panel(330,setup=setup)[0]['Cambio observado'],'Sin cambio observado')
        setup=self.fixture()+"DELETE FROM evaluation.results WHERE run_id='composition-reference';"
        self.assertEqual(self.panel(330,setup=setup),[])

if __name__=='__main__':unittest.main()
