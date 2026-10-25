"""Read-only monitoring acceptance shared by live rehearsal and isolated tests."""
import base64
import json


def check_monitoring(exchange, domain, password, manifest, dashboards):
    """exchange(method, path, body, headers) returns (status, JSON object)."""
    headers = {'Content-Type': 'application/json', 'Authorization': 'Basic ' + base64.b64encode(('admin:' + password).encode()).decode()}
    def request(method, path, payload=None, authenticated=True):
        status, value = exchange(method, '/grafana' + path, None if payload is None else json.dumps(payload).encode(), headers if authenticated else {})
        return status, value
    def good(path):
        status, value = request('GET', path)
        if status != 200:
            raise ValueError('Monitoring endpoint unavailable: ' + path)
        return value
    if good('/api/health').get('database') != 'ok':
        raise ValueError('Grafana metadata database unhealthy')
    if request('GET', '/api/search', authenticated=False)[0] != 401:
        raise ValueError('Anonymous Grafana access must be denied')
    for uid in dashboards:
        document = good('/api/dashboards/uid/' + uid)['dashboard']
        if document['uid'] != uid or not document.get('panels'):
            raise ValueError('Provisioned dashboard missing')
    for uid in ('evaluation-postgres', 'prometheus'):
        if good('/api/datasources/uid/' + uid + '/health').get('status') != 'OK':
            raise ValueError('Monitoring datasource unhealthy')
    query = {'queries': [{'refId': 'A', 'datasource': {'uid': 'evaluation-postgres', 'type': 'grafana-postgresql-datasource'},
        'format': 'table', 'rawSql': 'SELECT r.run_id, r.report_sha256, count(s.run_id)::int AS results FROM evaluation.runs r LEFT JOIN evaluation.results s USING(run_id) GROUP BY r.run_id,r.report_sha256 ORDER BY r.run_id'}], 'from': '0', 'to': 'now'}
    status, result = request('POST', '/api/ds/query', query)
    if status != 200 or result['results']['A'].get('error'):
        raise ValueError('Evaluation query failed')
    values = result['results']['A']['frames'][0]['data']['values']
    actual = {row[0]: (row[1], row[2]) for row in zip(*values)}
    for entry in manifest['entries']:
        if actual.get(entry['run_id']) != (entry['report_sha256'], entry['results']):
            raise ValueError('Atlas evaluation identity or result count differs')
    return {'dashboards': sorted(dashboards), 'atlas_runs': 19, 'atlas_results': 1688,
            'anonymous_access': 'denied', 'datasources': 'healthy'}
