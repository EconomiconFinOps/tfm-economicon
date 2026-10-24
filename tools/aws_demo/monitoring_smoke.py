"""Isolated Docker smoke test. No AWS, published ports, model calls or real secrets.

Runs on any explicitly selected Docker test engine. All containers have a unique
prefix; cleanup removes only those created here. Python standard library only.
"""
import argparse
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent.parent
PG = 'pgvector/pgvector:pg16@sha256:7b822b0aac60967beb1ea5e576b8602c94c300a157d187f385ae3e0da199b90a'
PYTHON = 'python:3.12-slim@sha256:d764629ce0ddd8c71fd371e9901efb324a95789d2315a47db7e4d27e78f1b0e9'


def docker(*args, input=None):
    result = subprocess.run(['docker', *args], input=input, capture_output=True, timeout=600)
    if result.returncode:
        raise RuntimeError('Docker test operation failed: ' + args[0] + '\n' + result.stderr.decode(errors='replace')[-3000:])
    return result.stdout.decode().strip()


def probe():
    from monitoring_checks import check_monitoring
    def exchange(method, path, body, headers):
        connection = http.client.HTTPConnection('127.0.0.1', 23000, timeout=10)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, json.loads(raw) if raw.startswith(b'{') else {}
        finally:
            connection.close()
    manifest = json.loads(Path('/test/manifest.json').read_text())
    dashboards = json.loads(Path('/test/dashboards.json').read_text())
    last = None
    for _ in range(45):
        try:
            proof = check_monitoring(exchange, 'localhost', 'c' * 64, manifest, dashboards)
            import base64
            headers = {'Content-Type': 'application/json', 'Authorization': 'Basic ' + base64.b64encode(('admin:' + 'c'*64).encode()).decode()}
            marker = Path('/test/preferences-set')
            if marker.exists():
                status, preferences = exchange('GET', '/grafana/api/user/preferences', None, headers)
                if status != 200 or preferences.get('homeDashboardUID') != 'economicon-assistant-evidence':
                    raise ValueError('Grafana preferences did not persist across restart')
                proof['preferences_retained'] = True
            else:
                status, _ = exchange('PUT', '/grafana/api/user/preferences', b'{"homeDashboardUID":"economicon-assistant-evidence"}', headers)
                if status != 200:
                    raise ValueError('Cannot set isolated persistence fixture')
                marker.touch()
            print(json.dumps(proof))
            return
        except (OSError, ValueError, KeyError, IndexError) as error:
            last = error
            time.sleep(2)
    raise RuntimeError('Monitoring acceptance failed: ' + str(last))


def main():
    prefix = 'economicon-atlas-test-' + uuid4().hex[:10]
    containers, images = [], []
    def run(suffix, *args):
        name = prefix + '-' + suffix
        docker('run', '-d', '--name', name, '--label', 'economicon.test=atlas', '--memory', '768m', '--cpus', '1', *args)
        containers.append(name)
        return name
    try:
        with tempfile.TemporaryDirectory(prefix='economicon-atlas-') as directory:
            context = Path(directory)
            shutil.copytree(ROOT / 'apps/monitoring', context / 'apps/monitoring')
            cert = context / 'apps/backend/app/resources/rds-eu-west-1.pem'
            cert.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'apps/backend/app/resources/rds-eu-west-1.pem', cert)
            for name in ('grafana', 'prometheus'):
                tag = prefix + ':' + name
                docker('build', '-q', '-f', str(context / f'apps/monitoring/aws/{name}.Dockerfile'), '-t', tag, str(context))
                images.append(tag)
            pg = run('pg', '--network', 'none', '-e', 'POSTGRES_USER=jup131', '-e', 'POSTGRES_PASSWORD=synthetic-local-test-only', '-e', 'POSTGRES_DB=embeddings', PG,
                     'bash', '-ec', 'openssl req -x509 -newkey rsa:2048 -nodes -keyout /tmp/server.key -out /tmp/server.crt -days 1 -subj /CN=localhost -addext subjectAltName=DNS:localhost,IP:127.0.0.1 >/dev/null 2>&1; chown postgres:postgres /tmp/server.key; chmod 600 /tmp/server.key; exec docker-entrypoint.sh postgres -p 25432 -c ssl=on -c ssl_cert_file=/tmp/server.crt -c ssl_key_file=/tmp/server.key')
            for attempt in range(30):
                ready = subprocess.run(['docker', 'exec', pg, 'pg_isready', '-p', '25432', '-U', 'jup131', '-d', 'embeddings'], capture_output=True)
                if ready.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Disposable PostgreSQL did not start')
            docker('exec', '-i', pg, 'psql', '-p', '25432', '-U', 'jup131', '-d', 'embeddings', '-v', 'ON_ERROR_STOP=1', input=(ROOT / 'apps/backend/app/aws_atlas_data/evaluations.sql').read_bytes())
            setup = f"CREATE ROLE grafana_evaluation_reader LOGIN PASSWORD '{'a'*64}'; GRANT USAGE ON SCHEMA evaluation TO grafana_evaluation_reader; GRANT SELECT ON ALL TABLES IN SCHEMA evaluation TO grafana_evaluation_reader; CREATE ROLE economicon_grafana LOGIN PASSWORD '{'b'*64}'; CREATE DATABASE grafana OWNER economicon_grafana;"
            docker('exec', '-i', pg, 'psql', '-p', '25432', '-U', 'jup131', '-d', 'embeddings', '-v', 'ON_ERROR_STOP=1', input=setup.encode())
            prom = run('prom', '--network', 'container:' + pg, '--read-only', '--tmpfs', '/prometheus:rw,uid=65534,gid=65534', '-e', 'MONITORING_NAMESPACE=economicon-test.internal', images[1])
            # Same application layers, with the isolated PostgreSQL test CA.
            # Production image continues to contain only the pinned AWS CA.
            docker('cp', pg + ':/tmp/server.crt', str(context / 'ca.pem'))
            (context / 'tls-test.Dockerfile').write_text('FROM ' + images[0] + '\nCOPY ca.pem /etc/grafana/rds-ca.pem\n')
            grafana_image = prefix + ':grafana-tls-test'
            docker('build', '-q', '-f', str(context / 'tls-test.Dockerfile'), '-t', grafana_image, str(context))
            images.append(grafana_image)
            name = prefix + '-grafana'
            env = {
                'GF_SERVER_HTTP_PORT': '23000', 'GF_SERVER_ROOT_URL': 'http://localhost:23000/grafana/', 'GF_SERVER_SERVE_FROM_SUB_PATH': 'true',
                'GF_AUTH_ANONYMOUS_ENABLED': 'false', 'GF_USERS_ALLOW_SIGN_UP': 'false', 'GF_SECURITY_ADMIN_PASSWORD': 'c'*64,
                'GF_SECURITY_SECRET_KEY': 'd'*64, 'GF_DATABASE_TYPE': 'postgres', 'GF_DATABASE_HOST': 'localhost:25432',
                'GF_DATABASE_NAME': 'grafana', 'GF_DATABASE_USER': 'economicon_grafana', 'GF_DATABASE_PASSWORD': 'b'*64,
                'GF_DATABASE_SSL_MODE': 'verify-full', 'GF_DATABASE_CA_CERT_PATH': '/etc/grafana/rds-ca.pem',
                'GRAFANA_EVALUATION_DB_HOST': 'localhost:25432', 'GRAFANA_EVALUATION_DB_PASSWORD': 'a'*64,
                'GF_ANALYTICS_REPORTING_ENABLED': 'false', 'GF_ANALYTICS_CHECK_FOR_UPDATES': 'false',
            }
            docker('create', '--name', name, '--network', 'container:' + pg, '--read-only', '--tmpfs', '/tmp:rw,mode=1777', '--memory', '768m', '--cpus', '1', *[arg for k,v in env.items() for arg in ('-e', k+'='+v)], grafana_image)
            containers.append(name)
            docker('start', name)
            helper = prefix + '-probe'
            docker('create', '--name', helper, '--network', 'container:' + pg, '--memory', '128m', '--cpus', '0.5', PYTHON, 'python', '/test/monitoring_smoke.py', '--probe')
            containers.append(helper)
            tests = context / 'test'; tests.mkdir()
            for file in ('monitoring_smoke.py', 'monitoring_checks.py'):
                shutil.copyfile(ROOT / 'tools/aws_demo' / file, tests / file)
            shutil.copyfile(ROOT / 'apps/backend/app/aws_atlas_data/manifest.json', tests / 'manifest.json')
            (tests / 'dashboards.json').write_text(json.dumps([json.loads(p.read_text(encoding='utf-8'))['uid'] for p in (ROOT / 'apps/monitoring/grafana/dashboards').glob('*.json')]), encoding='utf-8')
            docker('cp', str(tests), helper + ':/test')
            print(docker('start', '-a', helper), flush=True)
            if docker('inspect', '--format', '{{.State.ExitCode}}', helper) != '0':
                raise RuntimeError('Monitoring probe failed')
            docker('restart', name)
            print(docker('start', '-a', helper), flush=True)
            if docker('inspect', '--format', '{{.State.ExitCode}}', helper) != '0':
                raise RuntimeError('Monitoring restart probe failed')
            print('PASS: Grafana, TLS datasources, three dashboards, Atlas identities, anonymous denial and restart.', flush=True)
    except Exception:
        for name in containers:
            if name.endswith(('-grafana', '-prom')):
                result = subprocess.run(['docker', 'logs', '--tail', '30', name], capture_output=True)
                print((result.stdout + result.stderr).decode(errors='replace')[-6000:], flush=True)
        raise
    finally:
        for name in reversed(containers):
            subprocess.run(['docker', 'rm', '-f', '-v', name], capture_output=True)
        for name in images:
            subprocess.run(['docker', 'image', 'rm', name], capture_output=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', action='store_true')
    if parser.parse_args().probe:
        probe()
    else:
        main()
