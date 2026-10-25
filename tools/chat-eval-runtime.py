"""Read-only source/container hash verification on the authorized Docker host.

Does not build, deploy, read environment variables, renew keys or call a model.
Provider configuration and corpus database snapshots require separate checks.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

TOKENIZER = 'apps/processor/app/agents/prompt_resources/jup035/chat/v2/tokenizer.json'
FLASH_TOKENIZER = 'apps/processor/app/agents/prompt_resources/jup035/chat/v4/tokenizer.json'
TOKENIZER_BUILDER = 'apps/processor/build_tokenizer.py'
PROMPT_ROOT = 'apps/processor/app/agents/prompt_resources/jup035/'


def generated_hashes(plan):
    artifacts = plan.get('generated_artifacts', {})
    manifests = {PROMPT_ROOT + kind + '/v4/manifest.json' for kind in ('chat', 'summary')}
    # The frozen plan selects the contract; old plans never acquire v4 implicitly.
    native = any(name.startswith(PROMPT_ROOT + kind + '/v4/')
                 for name in plan['file_hashes'] for kind in ('chat', 'summary'))
    required = {TOKENIZER, FLASH_TOKENIZER} if native else {TOKENIZER}
    if (not isinstance(artifacts, dict) or set(artifacts) - required
            or artifacts and TOKENIZER_BUILDER not in plan['file_hashes']
            or TOKENIZER_BUILDER in plan['file_hashes'] and set(artifacts) != required
            or native and (TOKENIZER_BUILDER not in plan['file_hashes']
                           or not manifests.issubset(plan['file_hashes']))):
        raise ValueError('Missing or unknown generated runtime artifact')
    for name, pin in artifacts.items():
        if (name in plan['file_hashes'] or not isinstance(pin, dict)
                or set(pin) != {'revision', 'sha256', 'bytes'}
                or not isinstance(pin['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', pin['sha256'])
                or not isinstance(pin['revision'], str) or not re.fullmatch(r'[0-9a-f]{40}', pin['revision'])
                or type(pin['bytes']) is not int or pin['bytes'] <= 0):
            raise ValueError('Invalid generated runtime artifact pin')
    return {name:pin['sha256'] for name,pin in artifacts.items()}


def source_hashes(plan, source):
    generated_hashes(plan)
    root = Path(source).resolve()
    observed = {}
    for name, expected in plan['file_hashes'].items():
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Invalid source path')
        path = (root / name).resolve()
        if root not in path.parents:
            raise ValueError('Source escapes the archive directory')
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError('Source hash mismatch: ' + name)
        observed[name] = actual
    if not observed:
        raise ValueError('Empty source manifest')
    return observed


def container_paths(plan, service):
    if service not in ('backend', 'processor', 'frontend'):
        raise ValueError('Unsupported verification service')
    prefix = f'apps/{service}/' + ('src/' if service == 'frontend' else 'app/')
    target = '/workspace/apps/frontend/src/' if service == 'frontend' else '/app/app/'
    paths = {name: target + name[len(prefix):] for name in plan['file_hashes'] if name.startswith(prefix)}
    generated = generated_hashes(plan)
    if service in ('backend', 'processor'):
        for name in generated:
            paths[name] = ('/opt/economicon/chat/v4/tokenizer.json' if name == FLASH_TOKENIZER
                           else '/opt/economicon/chat/v3/tokenizer.json') if service == 'backend' else '/app/app/' + name[len('apps/processor/app/'):]
    if service == 'backend':
        prompt = 'apps/processor/app/agents/prompt_resources/jup035/'
        for name in plan['file_hashes']:
            if any(name.startswith(prompt + bundle + '/') for bundle in ('chat/v3', 'chat/v4')):
                paths[name] = '/opt/economicon/' + name[len(prompt):]
            elif name == prompt + 'chat/v2/tokenizer.json':
                paths[name] = '/opt/economicon/chat/v3/tokenizer.json'
            elif name.startswith(prompt + 'summary/'):
                paths[name] = '/opt/economicon/summary/' + name[len(prompt + 'summary/'):]
    if not paths:
        raise ValueError('No files for requested service')
    if any('..' in PurePosixPath(path).parts for path in paths.values()):
        raise ValueError('Invalid container path')
    return paths


def command(args, data=None):
    # Errors remain opaque: docker stderr may contain private host paths.
    result = subprocess.run(args, input=data, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError('Read-only container verification failed')
    return json.loads(result.stdout)


def verify_container(plan, service, container, project, run=command):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,200}', container):
        raise ValueError('Invalid container identifier')
    paths = container_paths(plan, service)
    template = ('{"id":{{json .Id}},"image":{{json .Image}},"running":{{json .State.Running}},'
                '"started_at":{{json .State.StartedAt}},'
                '"project":{{json (index .Config.Labels "com.docker.compose.project")}}}')
    inspect = ['docker', 'inspect', '--format', template, container]
    before = run(inspect)
    if not project or before.get('project') != project or before.get('running') is not True:
        raise ValueError('Container is not running in the expected isolated project')
    if service == 'frontend':
        script = ("const fs=require('fs'),crypto=require('crypto');"
                  "const paths=JSON.parse(fs.readFileSync(0,'utf8'));"
                  "console.log(JSON.stringify(Object.fromEntries(Object.entries(paths).map(([k,p])=>"
                  "[k,crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex')]))));")
        invocation = ['node', '-e', script]
    else:
        script = ('import json,sys,hashlib,pathlib; paths=json.load(sys.stdin); '
                  'print(json.dumps({k:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() '
                  'for k,p in paths.items()}))')
        invocation = ['python', '-c', script]
    actual = run(['docker', 'exec', '-i', container, *invocation], json.dumps(paths).encode())
    frozen_hashes = {**plan['file_hashes'], **generated_hashes(plan)}
    expected = {name: frozen_hashes[name] for name in paths}
    if actual != expected:
        raise ValueError('Running container code differs from frozen plan')
    after = run(inspect)
    if after != before:
        raise ValueError('Container changed during verification')
    return {'service': service, **before, 'verified_file_hashes': actual,
            'verified_generated_artifacts': plan.get('generated_artifacts', {})
            if service in ('backend', 'processor') else {}}
