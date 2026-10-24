"""New health panel keeps measured zero distinct from absent traffic, for both services."""
import json,unittest
from pathlib import Path
import test_evaluation_readability_section_c as support

def panels(items):
    for panel in items:
        yield panel
        yield from panels(panel.get('panels',[]))

class CompositionHTTPErrorRate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[2]
        dashboard=json.loads((root/'apps/monitoring/grafana/dashboards/assistant-evidence.json').read_text(encoding='utf8'))
        panel=next(p for p in panels(dashboard['panels']) if p['id']==903)
        cls.expressions={service:next(t['expr'] for t in panel['targets'] if service+'_http_requests_total' in t['expr']) for service in ('backend','processor')}
        cls.image=support.requerir_promtool()

    def check_case(self, statuses, expected):
        cases=[]
        for service,expr in self.expressions.items():
            series={service+'_http_requests_total{status_code="'+status+'"}':values for status,values in statuses.items()}
            if not series:series={'unrelated_counter':'0+1x10'}
            cases.append(support.caso(expr,series,expected))
        runner=support.TasaDeErrorConPromtoolTests()
        runner.imagen=self.image
        result=runner.ejecutar(cases)
        self.assertEqual(result.returncode,0,(result.stdout+result.stderr).decode('utf8','replace'))

    def test_traffic_without_5xx_is_measured_zero(self):
        self.check_case({'200':'0+10x10'},[0])

    def test_mixed_traffic_is_25_percent(self):
        self.check_case({'200':'0+30x10','500':'0+10x10'},[25])

    def test_only_5xx_is_100_percent(self):
        self.check_case({'503':'0+5x10'},[100])

    def test_no_traffic_has_no_sample(self):
        self.check_case({},[])


class CompositionRetrievalStates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[2]
        dashboard=json.loads((root/'apps/monitoring/grafana/dashboards/assistant-evidence.json').read_text(encoding='utf8'))
        cls.by_id={p['id']:p for p in panels(dashboard['panels'])}
        cls.image=support.requerir_promtool()

    def check_state(self, values, expected, temporal=None):
        series={'backend_'+name:pattern for name,pattern in values.items()}
        if not series:series={'unrelated_counter':'0+1x10'}
        cases=[support.caso(self.by_id[i]['targets'][0]['expr'],series,expected) for i in (904,5005)]
        if temporal is not None:
            cases += [support.caso(t['expr'],series,temporal) for t in self.by_id[8348]['targets']]
        runner=support.TasaDeErrorConPromtoolTests();runner.imagen=self.image
        result=runner.ejecutar(cases)
        self.assertEqual(result.returncode,0,(result.stdout+result.stderr).decode('utf8','replace'))

    def test_observed_zero_denominator_is_not_zero_percent(self):
        self.check_state({'assistant_queries_total':'0+0x10','retrieval_failures_total':'0+0x10','retrieval_empty_total':'0+0x10'},[-1],[])

    def test_absent_series_is_not_inferred_inactivity(self):
        self.check_state({},[],[])

    def test_completed_queries_without_retrieval_events_are_measured_zero(self):
        self.check_state({'assistant_queries_total':'0+10x10','retrieval_failures_total':'0+0x10','retrieval_empty_total':'0+0x10'},[0],[0])

    def test_missing_failure_counter_does_not_claim_observed_zero(self):
        self.check_state({'assistant_queries_total':'0+0x10','retrieval_empty_total':'0+0x10'},[],[])

    def test_nonzero_events_keep_the_original_denominator(self):
        series={'backend_assistant_queries_total':'0+30x10','backend_retrieval_failures_total':'0+10x10','backend_retrieval_empty_total':'0+5x10'}
        cases=[support.caso(self.by_id[i]['targets'][0]['expr'],series,[value]) for i,value in ((904,0.25),(5005,0.125))]
        runner=support.TasaDeErrorConPromtoolTests();runner.imagen=self.image
        result=runner.ejecutar(cases)
        self.assertEqual(result.returncode,0,(result.stdout+result.stderr).decode('utf8','replace'))

if __name__=='__main__':unittest.main()
