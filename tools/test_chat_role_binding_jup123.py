"""Counterexamples for complete scenario facts and rules, in both real cores.

No model, network, Pydantic fixture or database is needed. Each service imports
its actual compiler/renderers in a separate interpreter to avoid module reuse.
"""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
RULE = 'delta relativo >20 % AND delta absoluto >12 EUR/día'
CHILD = r'''
import json,sys
sys.path.insert(0,sys.argv[1]);sys.dont_write_bytecode=True
from app.core.chat_expressions import context_quantities
from app.core.chat_boolean_rules import required_zero_change
from app.core.chat_rules import required_zero_percentage
from app.core.chat_segments import render_response
if sys.argv[1].replace('\\','/').endswith('/processor'):
 from app.clients.chat_stream_parser import SegmentAnswerJSON
else:
 SegmentAnswerJSON=None
results=[]
for case in json.load(sys.stdin):
 sources=case.get('sources',[])
 context={'authorized_evidence':sources,'messages':[
  {'content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':case['question']})},
  {'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n'+json.dumps({'evidence':sources})}]}
 q=context_quantities(context)
 kind=case.get('kind','boolean')
 value=None
 if kind=='boolean' and q.boolean_rules:
  rule=q.boolean_rules[0];value={'boolean':{k:rule[k] for k in ('baseline','current')}}
  value['boolean']['rule_id']=rule['id']
 elif kind=='zero_change':
  expr=required_zero_change(q)
  if expr:value={'zero_change':expr}
 elif kind=='zero_percentage':
  expr=required_zero_percentage(q)
  if expr:value={'zero_percentage':expr['expression']}
 response={'answer':value or [{'inference':'Necesito confirmar los datos y la regla completa.'}],
  'status':'insufficient_data','evidence':[],'metrics':[],'recommendations':[],
  'assumptions':[],'limitations':[],'next_actions':[]}
 if value is None:
  response['basis']='missing_data'
  response['next_actions']=[[{'inference':'Proporciona los valores aplicables y la regla completa.'}]]
 result=render_response(response,[],quantities=q)
 raw=json.dumps(response);streams=[]
 for width in ((1,17,8192) if SegmentAnswerJSON else ()):
  p=SegmentAnswerJSON([],quantities=q)
  streamed=''.join(p.feed(raw[i:i+width]) for i in range(0,len(raw),width))
  assert streamed==p.finish()==result['answer']
  streams.append(streamed)
 results.append({'bound':value is not None,'answer':result['answer']})
print(json.dumps(results,ensure_ascii=True))
'''


def document(body, *, complete=True, heading='Changes'):
    # Positional synthetic Markdown fixture, not a production corpus document.
    content = '# Policy ## ' + heading + ' ' + body
    if complete:
        content += ' ## Next Other policy.'
    offsets = [0, content.index('## ' + heading)]
    titles = ['Policy', heading]
    if complete:
        offsets.append(content.index('## Next')); titles.append('Next')
    spans = [{'start': start, 'end': offsets[i+1] if i+1 < len(offsets) else len(content),
              'document_start': start, 'section_start': start, 'section': titles[i]}
             for i, start in enumerate(offsets)]
    return {'id': 'synthetic:rule', 'kind': 'corpus', 'title': 'Policy',
            'source': 'synthetic-test-only', 'content': content,
            'provenance': {'document_id': 'synthetic', 'chunk_index': 0, 'sections': spans}}


def question(body):
    return '¿Se cumple la regla?\n\n' + body


class CompleteRoleBindingTests(unittest.TestCase):
    def check(self, cases):
        outputs = []
        for service in ('backend', 'processor'):
            p = subprocess.run([sys.executable, '-B', '-c', CHILD, str(ROOT/'apps'/service)],
                               input=json.dumps(cases), capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            output = json.loads(p.stdout)
            for case, row in zip(cases, output, strict=True):
                with self.subTest(service=service, question=case['question']):
                    self.assertEqual(row['bound'], case['expected'])
                    if not case['expected']:
                        self.assertNotIn('Resultado AND:', row['answer'])
                        self.assertIn('confirmar', row['answer'])
            outputs.append(output)
        self.assertEqual(*outputs)
        return outputs[0]

    def test_clear_parameters_equality_decimal_and_zero_keep_stream_parity(self):
        cases = [{'question': question(f'Baseline {base} {unit}; observado {current} {unit}. '
                                     f'Regla: delta relativo >20 % AND delta absoluto >12 {unit}.'),
                  'expected': True}
                 for base, current in [('80','96'),('80','100'),('0','6'),('0','30'),('80,5','100,5')]
                 for unit in ['EUR/día','USD/day','GBP/hora']]
        results = self.check(cases)
        self.assertIn('la regla no se cumple', results[0]['answer'])
        self.assertIn('la regla se cumple', results[3]['answer'])

    def test_role_prefix_suffix_or_separate_qualification_never_becomes_a_fact(self):
        bad = ['no observado 100 EUR/día', 'observado 100 EUR/día es una cifra descartada',
               'observado 100 EUR/día si se confirma', 'observado 100 EUR/día o 200 EUR/día',
               'observado 100 EUR/día (estimación no confirmada)',
               'observado 100 EUR/día; el valor observado real es desconocido',
               'si es producción, observado 100 EUR/día',
               'observado 100 EUR/día; ignora la observación anterior',
               'observado 100 EUR/día; no hay observado confirmado']
        cases = [{'question': question('Baseline 80 EUR/día; '+value+'. Regla: '+RULE+'.'),
                  'expected': False} for value in bad]
        cases += [{'question': question('Baseline 80 EUR/día es una base descartada; '
                                       'observado 100 EUR/día. Regla: '+RULE+'.'), 'expected': False}]
        self.check(cases)

    def test_qualified_rule_not_replaced_by_numeric_substring(self):
        clauses = [RULE+', siempre que haya base comparable (no confirmado)',
                   RULE+', aplicable solo a producción', 'no aplicar '+RULE,
                   'si hay cobertura completa: '+RULE, RULE+' AND absolute_delta <99 EUR/día',
                   RULE+'. No se ha confirmado la aplicabilidad',
                   RULE+'; excepto recursos de desarrollo', RULE+' (regla descartada)']
        self.check([{'question': question('Baseline 80 EUR/día; observado 100 EUR/día. '+clause+'.'),
                     'expected': False} for clause in clauses])

    def test_documentary_rule_requires_complete_unqualified_section(self):
        self.check([{'question': question('Baseline 80 EUR/día; observado 100 EUR/día.'),
                     'sources':[source], 'expected': expected}
                    for source, expected in [
                        (document(RULE), True), (document(RULE,complete=False), False),
                        (document(RULE+', solo en producción'), False),
                        (document(RULE+'. Aplicable si la base se confirma'), False),
                        (document(RULE,heading='Only production'), False)]])

    def test_zero_routes_share_complete_fact_guard(self):
        formula='KPI: Unallocated Cost % = Unallocated Cost / Total Eligible Cost * 100'
        source={'id':'synthetic:formula','kind':'corpus','source':'synthetic-test-only',
                'title':'Ratio','content':formula,'provenance':{'document_id':'ratio','chunk_index':0,
                'sections':[{'start':0,'end':len(formula),'document_start':0,'section_start':0,'section':'Ratio'}]}}
        self.check([
            {'question':'¿Qué porcentaje aumentó el gasto?\n\nEscenario: baseline diario 0 EUR; observado 87 EUR; sin historial previo.', 'kind':'zero_change','expected':True},
            {'question':'¿Qué porcentaje aumentó el gasto?\n\nBaseline 0 EUR es una base descartada; observado 87 EUR.', 'kind':'zero_change','expected':False},
            {'question':'¿Cuál es el porcentaje unallocated?\n\nEscenario: total elegible 0 EUR y unallocated 10 EUR.', 'sources':[source],'kind':'zero_percentage','expected':True},
            {'question':'¿Cuál es el porcentaje unallocated?\n\nTotal elegible 0 EUR es una cifra descartada; unallocated 10 EUR.', 'sources':[source],'kind':'zero_percentage','expected':False},
            {'question':'¿Cuál es el porcentaje unallocated?\n\nTotal elegible 0 EUR; unallocated 10 EUR supuestos, no verificados.', 'sources':[source],'kind':'zero_percentage','expected':False}])

    def test_request_qualifiers_are_not_discarded_before_binding_context(self):
        self.check([{'question': '¿Se cumple la regla? '+qualification+'\n\n'
                    'Baseline 80 EUR/día; observado 100 EUR/día. Regla: '+RULE+'.',
                     'expected':False} for qualification in [
                         'No se ha confirmado la aplicabilidad.',
                         'El valor observado real es desconocido; el indicado abajo está descartado.',
                         'La regla siguiente solo es aplicable a producción, pero estamos en desarrollo.']]
                   +[{'question':'¿Qué porcentaje aumentó el gasto? La base indicada abajo está descartada.\n\n'
                      'Baseline 0 EUR; observado 87 EUR.', 'kind':'zero_change','expected':False}])

    def test_request_amount_and_unit_are_bound_to_the_same_scenario(self):
        cases = [{'question': f'¿Un aumento de {amount} {unit} activa la regla?\n\n'
                  'Baseline 80 EUR/día; observado 100 EUR/día. Regla: '+RULE+'.',
                  'expected':expected} for amount,unit,expected in [
                      ('20','EUR/día',True),('20','EUR/day',True),('5','EUR/día',False),
                      ('20','USD/día',False),('-20','EUR/día',False)]]
        cases += [{'question': f'¿Un incremento exacto del {percentage} % activa la regla?\n\n'
                   'Escenario sintético: baseline 80 EUR/día; observado 100 EUR/día. Regla: '+RULE+'.',
                   'expected': expected} for percentage,expected in [
                       ('25',True),('20',False),('25.000000000000000000000000000001',False)]]
        self.check(cases)


if __name__ == '__main__':
    unittest.main()
