"""PR156 integration: distinct assessment origins, populations and complete public diagnostics.

Uses the existing isolated PostgreSQL helper. Never loads the demonstration stack.
"""
from __future__ import annotations
from collections import Counter
import json,re,unittest
from pathlib import Path
import test_evaluation_composition as composition

class CampaignDataIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        composition.CompositionSQL.setUpClass.__func__(cls)
        cls.new_ids=[f'jup133-infra-jup070-a-r{i}-20261023' for i in (1,2,3)]+[f'jup133-infra-jup071-r{i}-20261023' for i in (1,2,3)]
    psql=composition.CompositionSQL.psql
    query=composition.CompositionSQL.query
    panel=composition.CompositionSQL.panel

    def test_selector_offers_judge_explicitly_only_when_it_exists(self):
        query=next(v['query'] for v in self.dashboard['templating']['list'] if v['name']=='assessment')
        self.assertEqual(self.query(query,campaign=self.new_ids[-1]),[{'__text':'Juez IA · provisional','__value':'llm'},{'__text':'Instrumento original','__value':'instrument'}])
        old='JUP-071-864a0d6dc666'
        self.assertEqual(self.query(query,campaign=old),[{'__text':'Instrumento original','__value':'instrument'}])
        campaigns=next(v['query'] for v in self.dashboard['templating']['list'] if v['name']=='campaign')
        choices=self.query(campaigns)
        self.assertEqual(choices[0]['__value'],self.new_ids[-1])
        self.assertTrue(set(self.new_ids)<={r['__value'] for r in choices})

    def test_judge_case_counts_are_not_original_rules_or_completed_counts(self):
        for run,expected in zip(self.new_ids,[(13,14,1,28),(8,17,3,28),(12,13,3,28),(11,16,2,29),(9,17,3,29),(7,21,1,29)]):
            for panel,count in zip((102,103,104),expected[:3]):
                with self.subTest(run=run,panel=panel):
                    self.assertEqual(self.panel(panel,campaign=run,assessment='llm')[0]['casos'],f'{count} / {expected[3]}')
        latest=self.new_ids[-1]
        self.assertEqual(self.panel(102,campaign=latest,assessment='instrument')[0]['casos'],'0 / 29')
        self.assertEqual(self.panel(103,campaign=latest,assessment='instrument')[0]['casos'],'8 / 29')
        self.assertEqual(self.panel(104,campaign=latest,assessment='instrument')[0]['casos'],'21 / 29')
        self.assertEqual(self.panel(2006,campaign=latest)[0]['Completadas / previstas'],'28 / 29')
        self.assertEqual(self.panel(2006,campaign=self.new_ids[0])[0]['Completadas / previstas'],'27 / 28')

    def test_missing_judge_does_not_fall_back_to_human_or_rules(self):
        old='JUP-071-864a0d6dc666'
        self.assertIsNone(self.panel(102,campaign=old,assessment='llm')[0]['casos'])
        self.assertIsNone(self.panel(102,campaign="x' OR TRUE --",assessment='llm')[0]['casos'])
        self.assertEqual(self.panel(304,campaign='not-loaded',assessment='llm'),[])

    def test_coverage_of_available_answers_does_not_hide_failed_operations(self):
        rows=self.panel(2011,campaign=self.new_ids[-1])
        by_name={r['Indicador']:r for r in rows}
        self.assertEqual(by_name['Respuestas revisadas / operaciones previstas']['Base'],'28 / 29')
        self.assertEqual(by_name['Respuestas revisadas / disponibles']['Base'],'28 / 28')
        self.assertEqual(by_name['Criterios revisados / aplicables']['Base'],'144 / 144')
        self.assertEqual(by_name['Disponibilidad de juicio humano']['Valor'],'No medido')
        self.assertNotEqual(by_name['Respuestas revisadas / operaciones previstas']['Valor'],by_name['Respuestas revisadas / disponibles']['Valor'])

    def test_semantic_points_and_human_not_measured_coexist(self):
        rows=self.panel(2009,campaign=self.new_ids[-1])
        required=[r for r in rows if r['Indicador']=='Puntos requeridos']
        self.assertEqual(len(required),2)
        judge=next(r for r in required if r['Tipo']=='Juez IA · provisional')
        human=next(r for r in required if r['Tipo']=='Registrado como humano · provisional')
        self.assertEqual(judge['Base'],'37 / 54')
        self.assertEqual(human['Valor'],'No medido')
        self.assertEqual(human['Base'],'0')
        self.assertNotEqual(judge['Valor'],human['Valor'])

    def test_retrieval_instrument_and_derived_judge_methods_are_separate(self):
        bank=self.panel(3008,campaign=self.new_ids[0])
        self.assertTrue(any(r['Indicador']=='Sección correcta' and r['Tipo']=='Juez IA · provisional' for r in bank))
        rob=self.panel(3008,campaign=self.new_ids[-1])
        self.assertEqual(next(r for r in rob if r['Indicador']=='Recuperación sin uso')['Base'],'13 / 27')
        self.assertEqual(self.panel(3002,campaign=self.new_ids[-1])[0]['Base observada'],'29 / 198')
        self.assertEqual(self.panel(3004,campaign=self.new_ids[-1])[0]['Base observada'],'29 / 29')

    def test_operation_latency_and_completed_only_latency_keep_different_populations(self):
        rows=self.panel(4010,campaign=self.new_ids[0])
        terminal=[r for r in rows if r['Población']=='Terminal · todas las operaciones']
        completed=[r for r in rows if r['Población']=='Terminal · sólo completadas']
        self.assertEqual(len(terminal),3);self.assertEqual(len(completed),3)
        self.assertEqual({r['Base'] for r in terminal},{28})
        self.assertEqual({r['Base'] for r in completed},{27})
        self.assertAlmostEqual(next(r['Segundos'] for r in terminal if r['Medida']=='Percentil 95 terminal'),144.176595)
        self.assertAlmostEqual(next(r['Segundos'] for r in completed if r['Medida']=='Percentil 95'),92.600543)
        self.assertIn('todas las operaciones',self.panel(8311,campaign=self.new_ids[0])[1]['Lectura'].casefold())

    def test_gateway_total_does_not_replace_reported_cost_or_historical_invoice(self):
        rows=self.panel(4006,campaign=self.new_ids[-1])
        total=next(r for r in rows if r['Indicador']=='Coste liquidado del gateway')
        self.assertEqual(total['Unidad'],'usd')
        self.assertAlmostEqual(float(total['Valor']),0.0743708712)
        reported=self.panel(4002,campaign=self.new_ids[-1])[0]['USD']
        self.assertAlmostEqual(reported,0.0014042112)
        self.assertNotAlmostEqual(reported*29,float(total['Valor']))
        self.assertEqual(self.panel(322,campaign=self.new_ids[-1]),self.panel(322,campaign=self.new_ids[0]))

    def test_measured_series_form_only_the_two_new_cohorts_and_distinct_latency_populations(self):
        for panel,n_points,n_lines,n_single in [(2101,310,38,196),(2102,28,0,28),(4101,24,6,6)]:
            rows=self.panel(panel)
            series=Counter(r['metric'] for r in rows)
            with self.subTest(panel=panel):
                self.assertEqual(len(rows),n_points)
                self.assertEqual(sum(n==3 for n in series.values()),n_lines)
                self.assertEqual(sum(n==1 for n in series.values()),n_single)
                self.assertTrue(all(n in (1,3) for n in series.values()))
        human=self.panel(2102)
        self.assertFalse(any('Juez IA' in r['metric'] for r in human))
        latency=self.panel(4101)
        self.assertTrue(any('todas las operaciones' in r['metric'] for r in latency))
        self.assertTrue(any('sólo completadas' in r['metric'] for r in latency))
        self.assertTrue(any('Etapa total del informe' in r['metric'] for r in latency))

    def test_same_declared_model_does_not_connect_historical_and_new_campaigns(self):
        kwargs={'campaign':self.new_ids[-1],'reference':'JUP-071-864a0d6dc666'}
        self.assertEqual(self.panel(311,**kwargs)[0]['Estado'],'No comparable')
        self.assertEqual(self.panel(330,**kwargs),[])
        new_pair={'campaign':self.new_ids[-1],'reference':self.new_ids[-2]}
        self.assertEqual(self.panel(311,**new_pair)[0]['Estado'],'Comparación disponible')
        rows=self.panel(330,**new_pair)
        self.assertTrue(any(r['grupo_interno']=='agent_cases' and r['Tipo']=='Juez IA · provisional' for r in rows))
        self.assertTrue(any(r['grupo_interno']=='cases' and r['Tipo']=='Automático registrado' for r in rows))
        self.assertFalse(any(r['Medida']=='Indicador del informe' for r in rows))

    def test_all_diagnostics_preserve_every_original_identity_and_hide_internal_labels(self):
        rows=self.panel(910)
        keys={(r['identidad_interna'],r['grupo_interno'],r['medida_interna'],r['variante_interna'],r['Estado']) for r in rows}
        actual=self.query('SELECT run_id,grp,metric_id,behavior,status FROM evaluation.results')
        self.assertEqual(len(rows),1670)
        self.assertEqual(keys,{(r['run_id'],r['grp'],r['metric_id'],r['behavior'],{'measured':'Medido','not_measured':'No medido','pass':'Favorable','fail':'Fallido','blocked':'Bloqueado','not_run':'Sin evaluar'}.get(r['status'],r['status'])) for r in actual})
        self.assertEqual(sum(r['grupo_interno'].startswith('agent_') for r in rows),504)
        for panel in (910,330):
            hidden=self.by_id[8303 if panel==330 else panel]['transformations'][0]['options']['excludeByName']
            for row in (rows if panel==910 else self.panel(330,campaign=self.new_ids[-1],reference=self.new_ids[-2])):
                for key,value in row.items():
                    if not hidden.get(key):self.assertNotRegex(str(value),r'agent_|JUP[- ]?\d|T-800|Johnny[ -]?5|47l45')

    def test_zero_latency_is_measured_while_missing_latency_is_not_fabricated(self):
        from evaluation_readability_support import insertar_ejecucion,insertar_resultado
        setup=insertar_ejecucion('latency-zero','JUP-070','2026-10-23T17:00:00Z')
        setup+=insertar_resultado('latency-zero','campaign_system','latency_p95',valor=0,unidad='ms',denominador=1)
        self.assertTrue(self.panel(4005,campaign='latency-zero',setup=setup)[0]['Tiempo hasta finalizar']=='0,00 s')
        missing=insertar_ejecucion('latency-missing','JUP-070','2026-10-23T17:00:00Z')
        missing+=insertar_resultado('latency-missing','campaign_system','latency_p95',estado='not_measured',unidad='ms',denominador=1)
        self.assertEqual(self.panel(4005,campaign='latency-missing',setup=missing),[])

    def test_campaign_metadata_states_the_actual_repetition_without_model_attestation(self):
        for index,run_id in enumerate(self.new_ids):
            with self.subTest(run_id=run_id):
                rows=self.panel(301,campaign=run_id)
                self.assertEqual(len(rows),1)
                self.assertEqual(rows[0]["Condiciones"],f"Repetición {index % 3 + 1} de 3 · provisional · ejecución del modelo no atestiguada")
        historical=self.panel(301,campaign="JUP-071-864a0d6dc666")
        self.assertEqual(historical[0]["Condiciones"],"Una repetición · provisional · ejecución del modelo no atestiguada")

    def test_configuration_annotations_preserve_each_change_type_and_empty_state(self):
        sql=self.by_id[8301]['targets'][5]['rawSql']
        expected=self.query('SELECT ch.run_at AS time,ch.annotation,ch.changes,r.source FROM evaluation.config_changes ch JOIN evaluation.runs r USING(run_id) ORDER BY ch.run_at')
        actual=self.query(sql)
        self.assertGreaterEqual(len(expected),5)
        self.assertGreaterEqual(len({tuple(row['changes']) for row in expected}),2)
        self.assertEqual([row['fecha_original'] for row in actual],[row['time'] for row in expected])
        for row,original in zip(actual,expected):
            with self.subTest(time=original['time']):
                self.assertEqual(row['Configuración · cambio'],original['annotation'])
                self.assertEqual(row['tipos_originales'].split(','),original['changes'])
                source={'JUP-070':'Banco','JUP-071':'Robustez'}.get(original['source'],'Histórico')
                self.assertEqual(row['Ámbito'],source)
                self.assertIn('sin atribución causal',row['Alcance'].casefold())
                self.assertNotRegex(row['Configuración · cambio']+' '+row['tipos_originales'],r'agent_|JUP[- ]?\d|T-800|Johnny[ -]?5|47l45')
        self.assertEqual(self.query(sql,setup='DELETE FROM evaluation.results; DELETE FROM evaluation.runs;'),[])

if __name__=='__main__':unittest.main()
