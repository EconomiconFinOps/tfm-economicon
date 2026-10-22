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

if __name__=='__main__':unittest.main()
