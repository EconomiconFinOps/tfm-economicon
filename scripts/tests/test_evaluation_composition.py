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
DASHBOARD=Path(os.environ.get('EVALUATION_COMPOSITION_DASHBOARD') or ROOT/'apps/monitoring/grafana/dashboards/assistant-evidence.json')

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
        self.assertEqual(self.by_id[110]['type'],'table')
        self.assertEqual(self.by_id[107]['options']['stacking'],'none')
        self.assertEqual(self.by_id[114]['type'],'xychart')
        self.assertEqual(len(self.by_id[114]['targets']),2)
        self.assertEqual(self.by_id[114]['fieldConfig']['defaults']['custom']['show'],'points')
        self.assertTrue({106,2101,2102,4101}.isdisjoint(self.by_id))
        for p in self.by_id.values():
            if p['type'] in ('text','row'):continue
            if p['type']=='alertlist':
                original=json.loads((DASHBOARD.parent/'technical-metrics.json').read_text(encoding='utf8'))
                self.assertEqual(p['options'],next(x['options'] for x in original['panels'] if x['type']=='alertlist'))
                continue
            self.assertIn(p['datasource']['uid'],('evaluation-postgres','prometheus'))
            self.assertTrue(all(t.get('datasource',p['datasource'])==p['datasource'] for t in p.get('targets',[])))
            self.assertTrue(all(t.get('refId') for t in p.get('targets',[])))

    def test_open_sections_unique_identity_and_compact_primary_cards(self):
        all_panels=list(panels(self.dashboard['panels']))
        self.assertEqual(len(all_panels),len(self.by_id))
        rows=[p for p in self.dashboard['panels'] if p['type']=='row']
        self.assertEqual([p['id'] for p in rows],[1000,2000,3000,4000,117])
        self.assertTrue(all(not p['collapsed'] for p in rows))
        groups={};current=None
        for p in self.dashboard['panels']:
            if p['type']=='row':current=p['id'];groups[current]=[]
            else:groups[current].append(p)
        for row,group in groups.items():
            cards=sorted((p for p in group if p['type']=='stat'),key=lambda p:p['gridPos']['x'])
            self.assertEqual(len(cards),4,row)
            self.assertEqual([p['gridPos']['x'] for p in cards],[0,6,12,18])
            self.assertEqual({p['gridPos']['w'] for p in cards},{6})
            self.assertEqual(len({p['gridPos']['y'] for p in cards}),1)
        for p in all_panels:
            g=p['gridPos'];self.assertGreater(g['h'],0);self.assertGreater(g['w'],0)
            self.assertLessEqual(g['x']+g['w'],24)
        for name,uid in [('assistant-evaluation.json','economicon-assistant-evaluation'),('technical-metrics.json','economicon-technical-metrics')]:
            self.assertEqual(json.loads((DASHBOARD.parent/name).read_text(encoding='utf8'))['uid'],uid)

    def test_operational_health_keeps_zero_absence_and_errors_distinct(self):
        note=self.by_id[8340]['options']['content']
        self.assertIn('Sin serie disponible',note)
        self.assertIn('base 0',note)
        self.assertIn('errores',note)
        self.assertNotIn('contadores presentes',note)
        for i in (902,903,904,5005,5006,5007,8348):
            self.assertEqual(self.by_id[i]['datasource']['uid'],'prometheus')
            self.assertNotIn('timeFrom',self.by_id[i])
        empty=self.by_id[8348]['gridPos'];alerts=self.by_id[5008]['gridPos']
        self.assertEqual((empty['w'],alerts['w']),(12,12))
        self.assertEqual(empty['y'],alerts['y'])
        self.assertEqual(len(self.by_id[8348]['targets']),2)
        for i in (904,5005):
            default=self.by_id[i]['fieldConfig']['defaults']
            self.assertEqual(default['noValue'],'Sin serie disponible')
            self.assertIn('Sin tasa',json.dumps(default['mappings'],ensure_ascii=False))

    def test_public_titles_text_and_help_have_no_internal_references(self):
        # R1/R2/R3 are approved repetition labels, not agent or task identifiers.
        bad=re.compile(r'JUP[- ]?\d|PR\d|bc94|c213|develop|T-800|Johnny[ -]?5|47l45|\bAgente\b|\bSHA\b',re.I)
        for p in list(self.by_id.values())+[self.dashboard]:
            for k in ('title','description'):
                self.assertNotRegex(p.get(k,''),bad)
            self.assertNotRegex(p.get('options',{}).get('content',''),bad)
            self.assertNotRegex(p.get('fieldConfig',{}).get('defaults',{}).get('noValue',''),bad)
        for v in self.dashboard['templating']['list']:
            self.assertNotRegex(v.get('current',{}).get('text',''),bad)
        self.assertFalse(self.dashboard.get('links'))

    def test_real_variable_values_are_sql_escaped_and_defaults_not_frozen(self):
        variables={v['name']:v for v in self.dashboard['templating']['list']}
        self.assertEqual(set(variables),{'campaign','assessment','reference','poblacion_tiempos','model_availability'})
        self.assertEqual(variables['model_availability']['hide'],2)
        self.assertTrue(variables['model_availability']['skipUrlSync'])
        self.assertFalse(variables['campaign']['current'])
        self.assertFalse(variables['assessment']['current'])
        self.assertEqual(variables['reference']['current']['value'],'__none__')
        self.assertEqual(variables['poblacion_tiempos']['current']['value'],'all')
        self.assertIn('__value',variables['campaign']['query'])
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
            self.assertRegex(p['fieldConfig']['defaults']['noValue'],r'^(No medido|Sin datos)(?:$|:)')
            for t in p.get('targets',[]):
                self.assertNotRegex(t.get('rawSql',''),r'(?i)coalesce\([^)]*,\s*0\s*\)')

    def test_complete_detail_options_keep_history_and_configuration_accessible(self):
        for i,count in ((8301,6),(8302,2),(8303,4)):
            p=self.by_id[i]
            self.assertEqual(p['type'],'table')
            self.assertEqual(len(p['targets']),count)
            self.assertEqual(p['options']['frameIndex'],0)
        for i,index in ((8301,3),(8301,4),(8303,3)):
            p=self.by_id[i];sql=p['targets'][index]['rawSql']
            self.assertEqual(p['timeFrom'],'30d')
            self.assertNotIn('${campaign',sql)
            self.assertIn('$__timeFilter(r.run_at)',sql)
            self.assertIn('x.value AS valor_original',sql)
            self.assertIn('r.run_at AS fecha_original',sql)
            hidden=p['transformations'][0]['options']['excludeByName']
            self.assertTrue(hidden['valor_original']);self.assertTrue(hidden['fecha_original'])
        config=self.by_id[8301]['targets'][5]['rawSql']
        self.assertIn('ch.annotation',config);self.assertIn('ch.changes',config)
        self.assertTrue(self.by_id[8301]['transformations'][0]['options']['excludeByName']['tipos_originales'])

    def test_detail_widths_and_inspection_keep_values_next_to_indicators(self):
        for i,name in ((8301,'Conducta · indicador'),(8302,'Campaña · indicador'),(8303,'Gateway · indicador')):
            p=self.by_id[i]
            order=p['transformations'][0]['options']['indexByName']
            self.assertLess(order[name],order['Valor']);self.assertLess(order['Valor'],order['Base'])
            fields={o['matcher']['options']:{x['id']:x['value'] for x in o['properties']} for o in p['fieldConfig']['overrides']}
            self.assertLessEqual(fields[name]['custom.width'],450)
            self.assertTrue(fields[name]['custom.inspect'])
            self.assertLessEqual(fields['Origen']['custom.width'],240)
            self.assertEqual(fields['Valor']['custom.width'],fields['Base']['custom.width'])
        self.assertEqual(self.by_id[8310]['type'],'barchart')
        self.assertEqual(self.by_id[8310]['fieldConfig']['defaults']['unit'],'suffix: s')
        self.assertIn('aproximadamente el 95 %',self.by_id[8311]['targets'][0]['rawSql'])

    def test_help_definitions_match_the_measure_and_its_population(self):
        contracts={
            1002:('precisión','detector','sintética','5/5'),
            1003:('cobertura','sintéticos','5/7'),
            1004:('detectables','sintéticos','5/5'),
            1005:('retraso','días','sintética','cero'),
            301:('campaña seleccionada','modelo declarado','fecha utc'),
            2006:('operaciones completadas','previstas','campaña seleccionada'),
            8301:('conducta','numéricos','no medido','base','juicio','campaña seleccionada'),
            3002:('fragmentos citados','fragmentos recuperados','campaña seleccionada'),
            3003:('muestras con recuperación','fragmentos recuperados','recuperaciones vacías','denominador','campaña seleccionada'),
            3004:('referencias válidas','referencias comprobadas','campaña seleccionada'),
            3005:('citas literales','citas comprobadas','campaña seleccionada'),
            8302:('recuperación','unidad','base','campaña seleccionada'),
            4002:('coste reportado','usd','campaña seleccionada','facturado'),
            4003:('entrada','unidades','campaña seleccionada'),
            4004:('salida','unidades','campaña seleccionada'),
            4005:('percentil 95','todas las operaciones','etapa total','segundos','campaña seleccionada'),
            322:('75 consultas','21–22 oct','facturado','estimación'),
            324:('75/75','0/124','consultas','intentos'),
            8303:('mediana','percentil 95','fase','segundos','campaña seleccionada'),
            5006:('trabajos de ingesta','creados','encolados','backend','publicación confirmada'),
            910:('todas las medidas','unidad','estado','base','juicio'),
            911:('todas las ejecuciones','procedencia','modelo declarado','fecha utc'),
        }
        for panel,concepts in contracts.items():
            help_text=self.by_id[panel]['description'].casefold()
            with self.subTest(panel=panel):
                for concept in concepts:self.assertIn(concept,help_text)
                self.assertNotRegex(help_text,r'100 consultas|100/100|3/924|6/924|3/15|0/55')
                self.assertNotIn('frescura simulada respecto al 30 oct',help_text)
        self.assertTrue(self.by_id[910]['transformations'][0]['options']['excludeByName']['variante_interna'])

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

    def query(self,sql,setup='',campaign='composition-current',reference='composition-reference',assessment='instrument',population='all'):
        sql=sql.replace('${campaign:sqlstring}',literal(campaign)).replace('${reference:sqlstring}',literal(reference)).replace('${assessment:sqlstring}',literal(assessment)).replace('${poblacion_tiempos:sqlstring}',literal(population))
        sql=re.sub(r'\$__timeFilter\([^)]*\)','TRUE',sql)
        result=self.psql('BEGIN;\n'+setup+'\nSET LOCAL ROLE grafana_evaluation_reader;\nSELECT COALESCE(jsonb_agg(to_jsonb(q)),\'[]\'::jsonb) FROM ('+sql+') q;\nROLLBACK;')
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(next(line for line in reversed(result.stdout.splitlines()) if line.startswith('[')))

    def panel(self,i,**kwargs):
        # Test projections follow the measures moved into native multi-frame tables.
        # They only rename actual returned fields; numeric values and dates stay raw.
        moved={2009:(8301,0),2010:(8301,1),2011:(8301,2),2101:(8301,3),2102:(8301,4),3008:(8302,0),4006:(8303,0),330:(8303,1),4010:(8303,2),4101:(8303,3),311:(8120,0)}
        panel,index=moved.get(i,(i,0))
        rows=self.query(self.by_id[panel]['targets'][index]['rawSql'],**kwargs)
        if i in (2101,2102,4101):
            field={2101:'Automático · indicador y contexto',2102:'Humano · indicador y contexto',4101:'Histórico · indicador y contexto'}[i]
            return [{'time':r['fecha_original'],'metric':r[field],'value':r['valor_original']} for r in rows]
        if i==311:return [{'Estado':r['estado_comparacion']} for r in rows]
        rename={2009:{'Conducta · indicador':'Indicador','Origen':'Tipo'},2010:{'Ausencias · control':'Control'},2011:{'Cobertura · indicador':'Indicador','Origen':'Tipo'},3008:{'Campaña · indicador':'Indicador','Origen':'Tipo'},4006:{'Gateway · indicador':'Indicador','Origen':'Tipo'},330:{'Cambios · medida':'Medida'},4010:{'Tiempos · medida':'Medida'}}.get(i,{})
        return [{rename.get(k,k):v for k,v in row.items()} for row in rows]


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
        for v in self.dashboard['templating']['list']:
            if v['type']=='query':self.query(v['query'],campaign=selected,reference='__none__')

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
        run='jup130-ai-cost-2026-10-21-to-2026-10-22'
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
        for i in (102,103,104):
            with self.subTest(panel=i):self.assertEqual(list(self.panel(i,campaign='not-loaded')[0].values()),[None])
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


    def test_current_campaign_is_dynamic_latest_robustness_including_missing_results(self):
        from evaluation_readability_support import insertar_ejecucion
        query=self.dashboard['templating']['list'][0]['query']
        setup=insertar_ejecucion('composition-next','JUP-071','2026-10-24T12:00:00Z')
        setup+=insertar_ejecucion('composition-newer-bank','JUP-070','2026-10-25T12:00:00Z')
        self.assertEqual(self.query(query,setup=setup)[0]['__value'],'composition-next')
        self.assertEqual(self.panel(102,setup=setup,campaign='composition-next'),[{'casos':None}])

    def test_citation_ratio_keeps_zero_but_rejects_absence_and_zero_base(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        s=insertar_ejecucion('composition-cites','JUP-071','2026-10-23T12:00:00Z')
        self.assertEqual(self.panel(3004,setup=s,campaign='composition-cites'),[])
        zero=s+insertar_resultado('composition-cites','rob_core','valid_citations',valor=0,numerador=0,denominador=4)
        self.assertEqual(self.panel(3004,setup=zero,campaign='composition-cites'),[{'Base observada':'0 / 4'}])
        empty=s+insertar_resultado('composition-cites','rob_core','valid_citations',valor=0,numerador=0,denominador=0)
        self.assertEqual(self.panel(3004,setup=empty,campaign='composition-cites'),[])
        missing=s+insertar_resultado('composition-cites','rob_core','valid_citations',estado='not_measured',denominador=4)
        self.assertEqual(self.panel(3004,setup=missing,campaign='composition-cites'),[])

    def test_citations_can_pass_while_whole_cases_fail(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado,insertar_casos
        s=insertar_ejecucion('composition-cites','JUP-071','2026-10-23T12:00:00Z')
        s+=insertar_casos('composition-cites',0,4)
        s+=insertar_resultado('composition-cites','rob_core','valid_citations',valor=1,numerador=4,denominador=4)
        self.assertEqual(self.panel(3004,setup=s,campaign='composition-cites')[0]['Base observada'],'4 / 4')
        self.assertEqual(self.panel(103,setup=s,campaign='composition-cites')[0]['casos'],'4 / 4')

    def test_detail_preserves_execution_state_unit_base_interval_and_judgment(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        s=''
        for run,judgment in [('composition-detail-a','human'),('composition-detail-b','automatic')]:
            s+=insertar_ejecucion(run,'JUP-071','2026-10-23T12:00:01Z')
            s+=insertar_resultado(run,'rob_core','valid_citations',valor=0.5,numerador=2,denominador=4,ci_bajo=0.2,ci_alto=0.8,juicio=judgment)
        s+=insertar_resultado('composition-detail-a','rob_system','cost_per_query',estado='not_measured',unidad='USD',juicio=None)
        rows=[r for r in self.panel(910,setup=s) if r['identidad_interna'].startswith('composition-detail-')]
        self.assertEqual(len(rows),3)
        measured=[r for r in rows if r['Estado']=='Medido']
        self.assertEqual(len({r['Ejecución'] for r in measured}),2)
        for r in measured:
            self.assertEqual(r['Unidad'],'tasa');self.assertEqual(r['Base'],'2 / 4')
            self.assertEqual(r['Intervalo'],'0.2 – 0.8')
            self.assertIn('12:00:01',r['Ejecución'])
        self.assertEqual({r['Origen del juicio'] for r in measured},{'Registrado como humano · provisional','Automático registrado'})
        missing=next(r for r in rows if r['Estado']=='No medido')
        self.assertEqual(missing['Valor'],'No medido')
        self.assertEqual(missing['Origen del juicio'],'No registrado')

    def test_reported_cost_and_billing_keep_distinct_names_and_units(self):
        rows=self.panel(910)
        self.assertTrue(any(r['Medida']=='Facturado por consulta' and r['Unidad']=='usd' for r in rows))
        self.assertTrue(any(r['Medida'].startswith('Coste reportado por operación') for r in rows))

    def evolution_fixture(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        # Aísla las cuatro identidades del escenario; la consulta termina en ROLLBACK.
        s='DELETE FROM evaluation.results; DELETE FROM evaluation.runs;\n'
        for run,date,milestone in [('composition-evo-a','2026-10-20T12:00:00Z',True),('composition-evo-b','2026-10-21T12:00:00Z',True),('composition-evo-nonmilestone','2026-10-22T12:00:00Z',False)]:
            s+=insertar_ejecucion(run,'JUP-071',date,clave='composition-evolution',hito=milestone)
            s+=insertar_resultado(run,'relevance','REL-1',valor=0.5,numerador=1,denominador=2)
            s+=insertar_resultado(run,'grounding','GRO-1',valor=0.5,numerador=1,denominador=2,juicio='human')
            s+=insertar_resultado(run,'latency','LAT-2','total',valor=1500,unidad='ms')
        s+=insertar_ejecucion('composition-evo-other','JUP-071','2026-10-23T12:00:00Z',clave='composition-other-context',hito=True)
        s+=insertar_resultado('composition-evo-other','relevance','REL-1',valor=1,numerador=2,denominador=2)
        return s

    def test_evolutions_separate_judgments_hitos_and_incompatible_singletons(self):
        s=self.evolution_fixture()
        automatic=[r for r in self.panel(2101,setup=s) if r['metric'].startswith('Documento correcto') and r['value']==0.5]
        human=[r for r in self.panel(2102,setup=s) if r['metric'].startswith('Fundamento registrado') and r['value']==0.5]
        self.assertGreaterEqual(len(automatic),3)
        self.assertEqual(len({r['metric'] for r in automatic}),1)
        self.assertGreaterEqual(len(human),2)
        self.assertFalse(any(r['time'].startswith('2026-10-22') for r in human))
        for r in automatic+human:self.assertNotIn('JUP-',r['metric'])
        singleton=[r for r in self.panel(2101,setup=s) if r['value']==1 and r['time'].startswith('2026-10-23')]
        self.assertEqual(len(singleton),1)
        self.assertNotIn(singleton[0]['metric'],{r['metric'] for r in automatic})

    def test_campaign_latency_keeps_ms_and_total_stage_separate_from_http(self):
        s=self.evolution_fixture()
        rows=[r for r in self.panel(4101,setup=s) if r['metric'].startswith('Percentil 95') and r['value']==1500]
        self.assertGreaterEqual(len(rows),3)
        self.assertTrue(all('Etapa total del informe' in r['metric'] for r in rows))
        self.assertEqual(self.panel(4101,setup='DELETE FROM evaluation.results;'),[])
        self.query(self.by_id[8301]['targets'][5]['rawSql'],setup=s)


    def test_singletons_and_two_incompatible_points_remain_visible_in_separate_series(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        setup='DELETE FROM evaluation.results; DELETE FROM evaluation.runs;'
        for run,date,key,value in [('a','2026-10-20T12:00:00Z','cohort-a',0.1),('b','2026-10-21T12:00:00Z','cohort-b',0.9)]:
            setup+=insertar_ejecucion(run,'JUP-071',date,clave=key,hito=True)
            setup+=insertar_resultado(run,'relevance','REL-1',valor=value,numerador=1,denominador=10)
        rows=self.panel(2101,setup=setup)
        self.assertEqual(len(rows),2)
        self.assertEqual({r['value'] for r in rows},{0.1,0.9})
        self.assertEqual(len({r['metric'] for r in rows}),2)
        single=setup+"DELETE FROM evaluation.runs WHERE run_id='b';"
        self.assertEqual(len(self.panel(2101,setup=single)),1)
        compatible=setup+"UPDATE evaluation.runs SET comparability_key='cohort-a' WHERE run_id='b';"
        pair=self.panel(2101,setup=compatible)
        self.assertEqual(len(pair),2)
        self.assertEqual(len({r['metric'] for r in pair}),1)

    def test_missing_date_value_wrong_unit_and_nonmilestone_do_not_create_points(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        setup='DELETE FROM evaluation.results; DELETE FROM evaluation.runs;'
        for run,date,value,unit,judgment,milestone in [('no-date',None,0.5,'tasa','automatic',True),('no-value','2026-10-20T12:00:00Z',None,'tasa','automatic',True),('wrong-unit','2026-10-20T12:00:00Z',0.5,'ms','automatic',True),('not-hito','2026-10-20T12:00:00Z',0.5,'tasa','human',False)]:
            setup+=insertar_ejecucion(run,'JUP-071',date,clave='same',hito=milestone)
            setup+=insertar_resultado(run,'relevance','REL-1',valor=value,unidad=unit,juicio=judgment,estado='not_measured' if value is None else 'measured')
        self.assertEqual(self.panel(2101,setup=setup),[])
        self.assertEqual(self.panel(2102,setup=setup),[])
        self.assertEqual(len(self.panel(910,setup=setup)),4)

    def test_latency_separates_judgment_and_variant_even_with_same_comparability_key(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        setup='DELETE FROM evaluation.results; DELETE FROM evaluation.runs;'
        for run,date,judgment in [('a','2026-10-20T12:00:00Z','automatic'),('b','2026-10-21T12:00:00Z','human')]:
            setup+=insertar_ejecucion(run,'JUP-071',date,clave='same')
            setup+=insertar_resultado(run,'latency','LAT-2','total',valor=1500,unidad='ms',juicio=judgment)
            setup+=insertar_resultado(run,'latency','LAT-1','generation',valor=2,unidad='ms',juicio=judgment)
        rows=self.panel(4101,setup=setup)
        self.assertEqual(len(rows),2)
        self.assertEqual(len({r['metric'] for r in rows}),2)
        self.assertTrue(all(r['value']==1500 for r in rows))


    def test_cohort_labels_identify_the_same_key_across_all_three_graphs(self):
        setup=self.evolution_fixture()
        auto=[r for r in self.panel(2101,setup=setup) if r['metric'].startswith('Documento correcto') and r['value']==0.5]
        human=[r for r in self.panel(2102,setup=setup) if r['metric'].startswith('Fundamento registrado') and r['value']==0.5]
        latency=[r for r in self.panel(4101,setup=setup) if r['metric'].startswith('Percentil 95') and r['value']==1500]
        labels=[{re.search(r'cohorte (\d+)',r['metric']).group(1) for r in rows} for rows in (auto,human,latency)]
        self.assertEqual(labels[0],labels[1]);self.assertEqual(labels[0],labels[2])
        self.assertEqual(len(labels[0]),1)

    def test_public_case_reference_keeps_original_only_in_hidden_field(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        setup=insertar_ejecucion('composition-public-case','JUP-070','2026-10-22T12:00:00Z')
        setup+=insertar_resultado('composition-public-case','grounding','GRD-2','JUP-069-008',valor=1,unidad='recuento')
        rows=[r for r in self.panel(910,setup=setup) if r['identidad_interna']=='composition-public-case']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['variante_interna'],'JUP-069-008')
        self.assertEqual(rows[0]['Variante'],'Referencia interna del informe')
        hidden=self.by_id[910]['transformations'][0]['options']['excludeByName']
        for key,value in rows[0].items():
            if not hidden.get(key):self.assertNotRegex(str(value),r'JUP[- ]?\d|T-800|Johnny[ -]?5|47l45')
        self.assertEqual(rows[0]['Valor'],'1')
        self.assertEqual(rows[0]['Unidad'],'recuento')

    def test_unknown_judgment_is_not_labelled_automatic(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        setup=insertar_ejecucion('composition-public-judgment','JUP-071','2026-10-22T12:00:00Z')
        for behavior,judgment in [('unknown',None),('automatic','automatic'),('human','human')]:
            setup+=insertar_resultado('composition-public-judgment','rob_core','required_coverage',behavior,valor=1,numerador=2,denominador=2,juicio=judgment)
        rows=self.panel(2009,setup=setup,campaign='composition-public-judgment')
        self.assertEqual(len(rows),3)
        self.assertEqual({r['Tipo'] for r in rows},{'No registrado','Automático registrado','Registrado como humano · provisional'})


    def test_latency_bars_separate_cohorts_and_populations_with_exact_units(self):
        query=self.by_id[8310]['targets'][0]['rawSql']
        rows=self.query(query,campaign='jup133-infra-jup071-r3-20261023')
        self.assertEqual(len(rows),3)
        for i,(r,p95) in enumerate(zip(rows,[106.865505,238.113623,62.960419]),1):
            self.assertTrue(r['Repetición UTC · base'].startswith('R'+str(i)+' · 23 oct'))
            self.assertIn('n=29',r['Repetición UTC · base'])
            self.assertAlmostEqual(r['p95 (s)'],p95)
        completed=self.query(query,campaign='jup133-infra-jup070-a-r3-20261023',population='completed')
        self.assertEqual(len(completed),3)
        for r,n,p95 in zip(completed,[27,25,25],[92.600543,59.869022,117.589775]):
            self.assertIn('n='+str(n),r['Repetición UTC · base'])
            self.assertAlmostEqual(r['p95 (s)'],p95)
        self.assertEqual(self.query(query,campaign='not-loaded'),[])

    def test_latency_bars_do_not_invent_a_value_or_mix_incompatible_runs(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        query=self.by_id[8310]['targets'][0]['rawSql']
        setup='DELETE FROM evaluation.results; DELETE FROM evaluation.runs;'
        for run,source,key,value in [('a','JUP-071','one',1000),('b','JUP-071','two',999000),('c','JUP-070','one',999000)]:
            setup+=insertar_ejecucion(run,source,'2026-10-20T12:00:00Z',clave=key)
            setup+=insertar_resultado(run,'campaign_system','latency_p95',valor=value,unidad='ms',denominador=1)
        rows=self.query(query,setup=setup,campaign='a')
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['p95 (s)'],1)
        self.assertIsNone(rows[0]['Mediana (s)'])
        self.assertEqual(self.query(query,setup=setup,campaign='a',population='completed'),[])
        self.assertEqual(self.query(query,setup=setup,campaign='a',population="all' OR TRUE --"),[])

    def test_p95_help_and_card_keep_terminal_population_and_measured_zero(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        run='p95-zero'
        setup=insertar_ejecucion(run,'JUP-071','2026-10-23T12:00:00Z')
        setup+=insertar_resultado(run,'campaign_system','latency_p95',valor=0,unidad='ms',denominador=2)
        self.assertEqual(self.panel(4005,setup=setup,campaign=run)[0]['Tiempo hasta finalizar'],'0,00 s')
        help_rows=self.panel(8311,setup=setup,campaign=run)
        self.assertIn('aproximadamente el 95 %',help_rows[0]['Lectura'])
        self.assertIn('Base: 2 operaciones',help_rows[1]['Lectura'])
        self.assertIn('incluidas fallidas',help_rows[1]['Lectura'])
        self.assertIn('No es media ni tiempo puro del LLM',help_rows[1]['Lectura'])

    def test_matrices_keep_real_counts_directions_zero_and_absent_measurements(self):
        robust='jup133-infra-jup071-r3-20261023'
        judge={r['Indicador']:r for r in self.panel(8101,campaign=robust)}
        for repetition,base in [('R1','11/29'),('R2','9/29'),('R3','7/29')]:
            self.assertTrue(judge['Favorables ↑'][repetition].endswith(base))
        self.assertTrue(judge['Favorables ↑']['R3'].startswith('D|'))
        self.assertTrue(judge['Sin evaluar ↓']['R3'].startswith('F|'))
        instrument={r['Indicador']:r for r in self.panel(8102,campaign=robust)}
        self.assertEqual(instrument['Favorables ↑']['R3'],'R|0,0% · 0/29')
        self.assertEqual(instrument['Disponibilidad HTTP ↑']['R3'],'N|No medido')
        bank={r['Indicador']:r for r in self.panel(8101,campaign='jup133-infra-jup070-a-r3-20261023')}
        for repetition,base in [('R1','13/28'),('R2','8/28'),('R3','12/28')]:
            self.assertTrue(bank['Favorables ↑'][repetition].endswith(base))

    def test_human_milestones_and_changes_do_not_invent_new_judgments_or_improvement(self):
        human=self.panel(8110)
        self.assertEqual(len(human),5)
        self.assertFalse(any((r['Fecha UTC'] or '').startswith('23 oct') for r in human))
        rows=self.panel(8121,campaign='jup133-infra-jup071-r3-20261023',reference='jup133-infra-jup071-r1-20261023',assessment='llm')
        self.assertEqual({r['Indicador']:r['Diferencia'] for r in rows},{'Favorables':'-4 casos','Fallidos':'+5 casos','Sin evaluar':'-1 caso'})
        for reference,label in [('__none__','Sin referencia'),('jup133-infra-jup070-a-r1-20261023','No comparable')]:
            unavailable=self.panel(8121,campaign='jup133-infra-jup071-r3-20261023',reference=reference,assessment='llm')
            self.assertEqual(len(unavailable),1)
            self.assertEqual(unavailable[0]['Indicador'],label)
            self.assertEqual(unavailable[0]['Antes'],'—')
            self.assertEqual(unavailable[0]['Ahora'],'—')

if __name__=='__main__':unittest.main()
