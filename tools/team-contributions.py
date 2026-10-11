#!/usr/bin/env python3
"""JUP-064: dated contribution evidence, read-only GitHub and Economicon bridge."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import unicodedata
from urllib.parse import quote

REPO = 'EconomiconFinOps/tfm-economicon'
TEAM = {'Iber1to': 'Alejandro Aguado', 'Victorh1397': 'Victor Mendez',
        'lmatsan': 'Lucia Mateo', 'ParisArcos': 'Paris Arcos Martin'}
ROLE_LABELS = {'leadership': 'Liderazgo', 'pairing': 'Pairing/coautoria',
               'review': 'Revision de PR', 'validation': 'Validacion, pruebas y documentacion'}
KIND_LABELS = {'review': 'revision', 'validation': 'validacion', 'other': 'review sin titulo'}
ARTIFACT_LABELS = {'documentation': 'documentacion', 'tests': 'pruebas'}
PR_STATE_LABELS = {'open': 'abierta', 'closed': 'cerrada sin integrar'}
ROLE_ALIASES = {'leadership': ['liderazgo', 'liderazgo asignado'],
                'pairing': ['pairing/coautoria', 'pairing y coautoria', 'pairing/coautoria y reconciliacion', 'pairing'],
                'review': ['revision de pr', 'revision pr', 'revision', 'revision de implementacion'],
                'validation': ['validacion, pruebas y documentacion', 'validacion/documentacion',
                               'validacion, pruebas y documentacion; auditoria', 'validacion funcional',
                               'validacion/evidencia']}
NAME_ALIASES = {**{normalize_name: login for login, normalize_name in
                   [('Iber1to', 'alejandro aguado'), ('Victorh1397', 'victor mendez'),
                    ('lmatsan', 'lucia mateo'), ('ParisArcos', 'paris arcos martin')]},
                'paris arcos': 'ParisArcos'}
BRIDGE_READ = '''import json
from collaboration import Settings, TrelloClient
c = TrelloClient(Settings.from_env())
print(json.dumps({'cards': c.get_cards()}, ensure_ascii=False))
'''


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower())
                   if unicodedata.category(c) != 'Mn').strip()


def run_json(args, input_text=None):
    result = subprocess.run(args, input=input_text.encode('utf-8') if input_text else None,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # CalledProcessError would hide what the source said; its own message is the useful part.
        raise RuntimeError(f'{" ".join(args[:3])} exited {result.returncode}: '
                           + result.stderr.decode('utf-8', 'replace').strip()[-2000:])
    return json.loads(result.stdout.decode('utf-8-sig'))


def github(endpoint, paginate=False):
    args = ['gh', 'api', f'repos/{REPO}/{endpoint}']
    if paginate:
        pages = run_json(args + ['--paginate', '--slurp'])
        return [item for page in pages for item in page]
    return run_json(args)


def login_of(item, key='user'):
    # A deleted account arrives as null; team logins keep the spelling of TEAM whatever case the source uses.
    login = ((item or {}).get(key) or {}).get('login')
    return next((member for member in TEAM if login and member.casefold() == login.casefold()), login)


def assigned_roles(text):
    roles = {}
    for key, aliases in ROLE_ALIASES.items():
        matches = re.findall(r'^\s*-\s*(?:' + '|'.join(re.escape(a) for a in aliases) + r')\s*:\s*(.+)$',
                             normalize(text), re.M)
        # Unknown or ambiguous identities remain visible and uncredited.
        people = set()
        for match in matches:
            name = match.strip('* `')
            people.add(next((login for alias, login in NAME_ALIASES.items()
                            if re.match(re.escape(alias) + r'(?=\s*(?:$|[.,;(]))', name)), None))
        roles[key] = next(iter(people)) if len(people) == 1 else None
    return roles


def role_lines(text):
    labels = '|'.join(re.escape(label) for aliases in ROLE_ALIASES.values() for label in aliases)
    return [line.strip() for line in text.splitlines()
            if re.match(r'^\s*-\s*(?:' + labels + r')\s*:', normalize(line))]


def review_kind(body, jup):
    # Same title rule as the JUP reviews check (tools/pr-policy.mjs): a prefix of the body, any suffix allowed.
    text = unicodedata.normalize('NFC', body).casefold()
    for kind, title in [('review', 'revisi[oó]n'), ('validation', 'validaci[oó]n')]:
        if re.match(r'[\s\ufeff]*' + title + r'[\s\ufeff]+' + re.escape(jup.casefold()) + r'(?![0-9a-z_])', text):
            return kind
    return 'other'


def declared_coauthors(message):
    # A trailer may give the full name, the login or a GitHub noreply address; any other email is never read.
    found = set()
    for name, email in re.findall(r'^[ \t]*co-authored-by:[ \t]*([^<\n]*)<([^<>\s]*)>', message, re.I | re.M):
        noreply = re.fullmatch(r'(?:\d+\+)?([^@+]+)@users\.noreply\.github\.com', email, re.I)
        keys = {name.strip().casefold(), noreply[1].casefold() if noreply else ''}
        people = {login for login in TEAM if login.casefold() in keys} | {NAME_ALIASES.get(normalize(name))} - {None}
        # Two different people in one trailer stay uncredited, like any ambiguous identity.
        if len(people) == 1:
            found |= people
    return sorted(found)


def collect_pr(pr):
    number = pr['number']
    detail = github(f'pulls/{number}')
    ids = sorted(set(re.findall(r'JUP-\d{3}', detail['title'] + ' ' + detail['head']['ref'])))
    commits = github(f'pulls/{number}/commits?per_page=100', True)
    reviews = github(f'pulls/{number}/reviews?per_page=100', True)
    comments = github(f'issues/{number}/comments?per_page=100', True)
    files = github(f'pulls/{number}/files?per_page=100', True)
    # Checks evidence is shared CI; it is never attributed to an individual validator.
    pages = run_json(['gh', 'api', f'repos/{REPO}/commits/{detail["head"]["sha"]}/check-runs?per_page=100',
                      '--paginate', '--slurp'])
    checks = [c for p in pages for c in p['check_runs']]
    return {'number': number, 'jups': ids, 'url': detail['html_url'],
            'author': login_of(detail), 'state': detail['state'],
            'draft': detail['draft'], 'merged_at': detail['merged_at'], 'head': detail['head']['sha'],
            'declared_roles': assigned_roles(detail.get('body') or ''),
            'role_source_lines': role_lines(detail.get('body') or ''),
            'commits': [{'url': c['html_url'], 'sha': c['sha'],
                         'author': login_of(c, 'author'),
                         'declared_coauthors': declared_coauthors((c.get('commit') or {}).get('message') or '')}
                        for c in commits],
            'reviews': [{'url': r['html_url'], 'author': login_of(r),
                         'state': r['state'], 'head': r['commit_id'], 'date': r['submitted_at'],
                         'kinds': {jup: review_kind(r.get('body') or '', jup) for jup in ids}}
                        for r in reviews if r['state'] != 'PENDING'],
            'comments': [{'url': c['html_url'], 'author': login_of(c),
                          'date': c['created_at'], 'updated_at': c['updated_at']}
                         for c in comments],
            'artifacts': [{'path': f['filename'], 'url': f'https://github.com/{REPO}/blob/{detail["head"]["sha"]}/{quote(f["filename"], safe="/")}',
                           'kind': 'documentation' if f['filename'].startswith(('docs/', 'openspec/')) else 'tests'}
                          for f in files if f['status'] != 'removed' and
                          (f['filename'].startswith(('docs/', 'openspec/')) or
                           re.search(r'(^|/)(tests?/|test_)|[.-]test[.-]', f['filename']))],
            'checks': [{'name': c['name'], 'status': c['status'], 'conclusion': c['conclusion'],
                        'url': c['html_url'], 'head': c['head_sha']} for c in checks]}


def build_snapshot(cards, prs, captured_at):
    stories = []
    for card in cards:
        match = re.match(r'^(JUP-\d{3})\b', card['name'])
        if not match:
            continue
        jup = match[1]
        stories.append({'jup': jup, 'trello': card['shortUrl'],
                        'assigned_roles': assigned_roles(card.get('desc', '')),
                        'role_source_lines': role_lines(card.get('desc', '')),
                        'prs': [p for p in prs if jup in p['jups']]})
    return {'schema_version': 1, 'captured_at': captured_at, 'repository': REPO,
            'team': TEAM, 'stories': sorted(stories, key=lambda s: s['jup'])}


def member_evidence(story, login):
    evidence = []
    for pr in story['prs']:
        if pr['author'] == login:
            evidence.append(('PR publicada', pr['url']))
        for commit in pr['commits']:
            if commit['author'] == login:
                evidence.append(('commit', commit['url']))
            if login in commit['declared_coauthors']:
                evidence.append(('coautoria declarada', commit['url']))
        for review in pr['reviews']:
            if review['author'] == login and review['state'] != 'PENDING':
                # GitHub stores an author's replies in review threads as a review; it never reviews their own PR.
                label = ('intervencion del autor en su PR' if login == pr['author']
                         else KIND_LABELS[review['kinds'].get(story['jup'], 'other')])
                suffix = ' / SHA anterior' if review['head'] != pr['head'] else ''
                evidence.append((f'{label}: {review["state"]}{suffix}', review['url']))
        for comment in pr.get('comments', []):
            if comment['author'] == login:
                evidence.append(('comentario de PR / ' + comment['date'][:10], comment['url']))
    return list(dict.fromkeys(evidence))


def role_gaps(story):
    gaps = []
    # A pull request closed without merging stays listed, but it is not current evidence of any role.
    prs = [p for p in story['prs'] if p.get('state') != 'closed' or p.get('merged_at')]
    for role in ROLE_LABELS:
        login = story['assigned_roles'].get(role)
        if login is None:
            gaps.append(f'{ROLE_LABELS[role]}: identidad sin resolver')
            continue
        if role == 'leadership':
            present = any(p['author'] == login for p in prs)
        elif role == 'pairing':
            present = any(c['author'] == login or login in c['declared_coauthors']
                          for p in prs for c in p['commits'])
        else:
            present = any(r['author'] == login and r['author'] != p['author'] and
                          r['kinds'].get(story['jup']) == role and
                          r['state'] in ('APPROVED', 'COMMENTED') and r['head'] == p['head']
                          for p in prs for r in p['reviews'])
        if not present:
            gaps.append(f'{ROLE_LABELS[role]}: sin evidencia estructurada actual de {TEAM[login]}')
    for pr in story['prs']:
        if pr['declared_roles'] != story['assigned_roles']:
            gaps.append(f'PR #{pr["number"]}: roles declarados difieren de Trello actual')
        # Keep any unresolved request visible; this is not a merge decision engine.
        latest = {}
        for review in sorted(pr['reviews'], key=lambda r: r.get('date') or ''):
            if review['state'] in ('CHANGES_REQUESTED', 'APPROVED'):
                latest[review['author']] = review['state']
        if 'CHANGES_REQUESTED' in latest.values():
            gaps.append(f'PR #{pr["number"]}: cambios solicitados pendientes')
    return gaps


def render(snapshot):
    lines = ['# Registro de contribuciones — JUP-064', '',
             f'Corte UTC: {snapshot["captured_at"]}. Fuente: integración Economicon y GitHub, solo lectura.', '',
             'Este registro acredita la existencia de acciones enlazadas, no su suficiencia ni el cumplimiento de una historia. '
             'Trello mantiene las asignaciones actuales; las PR conservan las declaraciones históricas. '
             'Una coautoría es declarada; un commit no demuestra por sí solo pairing. '
             'Una review titulada no demuestra por sí sola que sus criterios fueron probados. '
             'Los checks son CI compartida y los archivos son artefactos, nunca pruebas atribuidas a una persona. '
             'Los comentarios acreditan una intervención atribuible, no una review formal ni una validación vigente. '
             'SHA anterior, cambios solicitados y diferencias de roles requieren contraste humano. '
             'Las notas de pairing en Trello y contribuciones fuera de PR no se importan: su ausencia aquí no prueba ausencia de trabajo.', '',
             '## Participación por miembro', '',
             'Las columnas de roles cuentan asignaciones actuales, no acciones realizadas.', '',
             '| Persona | Historias con acciones | Liderazgo | Pairing | Revisión | Validación |',
             '| --- | --- | --- | --- | --- | --- |']
    for login, name in TEAM.items():
        count = sum(bool(member_evidence(s, login)) for s in snapshot['stories'])
        assignments = [sum(s['assigned_roles'].get(role) == login for s in snapshot['stories'])
                       for role in ROLE_LABELS]
        lines.append(f'| {name} (`{login}`) | {count} | ' + ' | '.join(map(str, assignments)) + ' |')
    for story in snapshot['stories']:
        lines += ['', f'## {story["jup"]}', '', f'[Tarjeta]({story["trello"]})', '',
                  '| Persona | Rol actual en Trello | Acciones observadas |', '| --- | --- | --- |']
        for login, name in TEAM.items():
            roles = ', '.join(ROLE_LABELS[r] for r, person in story['assigned_roles'].items() if person == login) or 'Sin asignación'
            evidence = member_evidence(story, login)
            links = '<br>'.join(f'[{label}]({url})' for label, url in evidence[:12]) or 'Pendiente de enlazar / no importado'
            if len(evidence) > 12:
                links += f'<br>[{len(evidence) - 12} acciones adicionales en snapshot](JUP-064-snapshot.json)'
            lines.append(f'| {name} | {roles} | {links} |')
        for pr in story['prs']:
            state = ('integrada' if pr['merged_at'] else 'borrador' if pr['draft'] and pr['state'] != 'closed'
                     else PR_STATE_LABELS.get(pr['state'], pr['state']))
            lines += ['', f'### [PR #{pr["number"]}]({pr["url"]}) — {state}', '',
                      f'HEAD: `{pr["head"]}`. Autor: `{pr["author"] or "cuenta eliminada"}`.', '',
                      'Roles declarados en la PR: ' + '; '.join(f'{ROLE_LABELS[r]}: {TEAM.get(p, "sin resolver")}' for r, p in pr['declared_roles'].items()) + '.', '',
                      'Artefactos (existencia, sin atribución de ejecución):']
            selected = []
            for kind in ('documentation', 'tests'):
                artifacts = [a for a in pr['artifacts'] if a['kind'] == kind]
                artifacts.sort(key=lambda a: (not a['path'].startswith('docs/evidence/'), a['path']))
                selected += artifacts[:3]
            lines += [f'- [{ARTIFACT_LABELS[a["kind"]]}: {a["path"]}]({a["url"]})' for a in selected] or ['- Sin artefactos importados.']
            if len(pr['artifacts']) > len(selected):
                lines.append(f'- [{len(pr["artifacts"]) - len(selected)} artefactos adicionales con enlaces originales en snapshot](JUP-064-snapshot.json).')
            lines += ['', 'Checks del HEAD (CI compartida):']
            lines += [f'- [{c["name"]}]({c["url"]}): {c["status"]} / {c["conclusion"] or "pendiente"}' for c in pr['checks']] or ['- Sin checks publicados en el HEAD.']
        lines += ['', 'Pendientes de contraste:']
        gaps = role_gaps(story)
        lines += [f'- {g}' for g in gaps] or ['- Sin huecos estructurados detectados; falta valorar contenido y pairing con el equipo.']
    return '\n'.join(lines) + '\n'


def write_atomic(path, text):
    # Readers see either the previous file or the complete new one, with the same bytes on every system.
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(text, encoding='utf-8', newline='\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collect', action='store_true', help='Read live sources; never writes to Trello/GitHub')
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.collect:
        cards = run_json(['ssh', '-o', 'ConnectTimeout=15', 'DockerServer', 'cd /home/danteadmin/economicon-collaboration && '
                          'docker compose run --rm -T --entrypoint python collaboration -'], BRIDGE_READ)['cards']
        prs = github('pulls?state=all&per_page=100', True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            prs = list(pool.map(collect_pr, prs))
        snapshot = build_snapshot(cards, prs, datetime.now(timezone.utc).isoformat())
    else:
        snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
        if snapshot['schema_version'] != 1 or snapshot['team'] != TEAM:
            raise ValueError('Unsupported snapshot schema or identity mapping')
    # Render first: a snapshot that cannot be rendered must not replace the versioned one.
    report = render(snapshot)
    if args.collect:
        write_atomic(args.snapshot, json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    write_atomic(args.output, report)
    print(f'{len(snapshot["stories"])} historias; {sum(len(s["prs"]) for s in snapshot["stories"])} PR vinculadas; {args.output}')


if __name__ == '__main__':
    main()
