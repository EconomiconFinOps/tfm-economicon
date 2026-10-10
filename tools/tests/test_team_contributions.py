import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unicodedata
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('contributions', Path(__file__).parents[1] / 'team-contributions.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ContributionTests(unittest.TestCase):
    def story(self):
        return {'jup': 'JUP-064', 'trello': 'https://trello.com/c/wluz6AGW',
                'assigned_roles': {'leadership': 'Victorh1397', 'pairing': 'Iber1to',
                                   'review': 'lmatsan', 'validation': 'ParisArcos'}, 'prs': []}

    def pr(self):
        return {'number': 1, 'author': 'Victorh1397', 'url': 'https://github.com/example/pull/1',
                'head': 'current', 'commits': [], 'reviews': [],
                'declared_roles': self.story()['assigned_roles']}

    def review(self, **changes):
        return dict({'url': 'review-url', 'author': 'ParisArcos', 'state': 'APPROVED',
                     'head': 'current', 'kinds': {'JUP-064': 'validation'}}, **changes)

    def main(self, *argv):
        with mock.patch('sys.argv', ['team-contributions.py', *map(str, argv)]), contextlib.redirect_stdout(io.StringIO()):
            m.main()

    def collect(self, detail=None, **pages):
        pages['pulls/7'] = dict({'title': 'feat(JUP-064): x', 'head': {'ref': 'feat/JUP-064-x', 'sha': 'current'},
                                 'html_url': 'pr-url', 'user': {'login': 'Victorh1397'}, 'state': 'open',
                                 'draft': False, 'merged_at': None, 'body': ''}, **(detail or {}))

        def github(endpoint, paginate=False):
            return pages[endpoint] if endpoint in pages else pages.get(endpoint.split('/')[2].split('?')[0], [])

        with mock.patch.object(m, 'github', github), mock.patch.object(m, 'run_json', return_value=[{'check_runs': []}]):
            return m.collect_pr({'number': 7})

    def missing(self, story, role):
        return any(g.startswith(m.ROLE_LABELS[role] + ': sin evidencia') for g in m.role_gaps(story))

    def test_assignment_alone_never_credits_participation(self):
        story = self.story()
        self.assertEqual(m.member_evidence(story, 'Iber1to'), [])
        self.assertEqual(len(m.role_gaps(story)), 4)

    def test_accented_roles_and_unknown_identity(self):
        roles = m.assigned_roles('- Revisión de PR: Lucia Mateo\n- Pairing/coautoría: Someone else')
        self.assertEqual(roles['review'], 'lmatsan')
        self.assertIsNone(roles['pairing'])

    def test_title_must_match_story_and_open_the_review(self):
        self.assertEqual(m.review_kind('Validación JUP-064\nEvidence', 'JUP-064'), 'validation')
        for text in ['Validacion JUP-065', 'I did Validacion JUP-064', 'Validacion JUP-0640', '# Validacion JUP-064',
                     'Validacion JUP-064_bis', 'Validacion JUP-06', 'Validacion: JUP-064', 'ValidacionJUP-064', '']:
            self.assertEqual(m.review_kind(text, 'JUP-064'), 'other', text)

    def test_title_accepts_the_suffixes_the_jup_reviews_check_accepts(self):
        for text in ['Validacion JUP-064 (revalidacion incremental sobre a1bbe89)', 'Validación JUP-064: favorable',
                     'VALIDACION  JUP-064.', '\n  validacion jup-064\nEvidence']:
            self.assertEqual(m.review_kind(text, 'JUP-064'), 'validation', text)
        for text in ['Revision JUP-064: ok', 'Revisión JUP-064 - incremental', 'Revision JUP-064']:
            self.assertEqual(m.review_kind(text, 'JUP-064'), 'review', text)
        self.assertEqual(m.review_kind(unicodedata.normalize('NFD', 'Revisión JUP-064: ok'), 'JUP-064'), 'review')
        self.assertEqual(m.review_kind('Revision JUP-064: ok', 'JUP-065'), 'other')

    def test_aliases_explanations_and_ambiguous_assignments(self):
        roles = m.assigned_roles('- Revisión PR: Víctor Méndez.\n'
                                 '- Pairing y coautoría: Paris Arcos Martin.\n'
                                 '- Validación/documentación: Alejandro Aguado (sustituye a Paris)')
        self.assertEqual(roles['review'], 'Victorh1397')
        self.assertEqual(roles['pairing'], 'ParisArcos')
        self.assertEqual(roles['validation'], 'Iber1to')
        self.assertIsNone(m.assigned_roles('- Liderazgo: Victor Mendez\n- Liderazgo: Lucia Mateo')['leadership'])
        self.assertIsNone(m.assigned_roles('- Liderazgo: Victor MendezUnknown')['leadership'])
        text = '- Revision: Lucia Mateo\n- Pairing: Victor Mendez\n- Validation details: not a role'
        self.assertEqual(m.assigned_roles(text), m.assigned_roles('\n'.join(m.role_lines(text))))

    def test_old_head_and_self_review_are_not_current_role_evidence(self):
        for review in [self.review(head='old'), self.review(author='Victorh1397')]:
            story = self.story(); pr = self.pr(); pr['reviews'] = [review]; story['prs'] = [pr]
            self.assertTrue(any(g.startswith('Validacion, pruebas y documentacion:') for g in m.role_gaps(story)))

    def test_comment_does_not_lift_request_changes(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr['reviews'] = [self.review(state='CHANGES_REQUESTED'), self.review(state='COMMENTED')]
        self.assertTrue(any('cambios solicitados' in g for g in m.role_gaps(story)))
        pr['reviews'].append(self.review())
        self.assertFalse(any('cambios solicitados' in g for g in m.role_gaps(story)))

    def test_commit_and_declared_coauthor_are_different_evidence(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr['commits'] = [{'url': 'commit-url', 'author': 'Victorh1397', 'declared_coauthors': ['Iber1to']}]
        self.assertEqual(m.member_evidence(story, 'Iber1to'), [('coautoria declarada', 'commit-url')])
        self.assertEqual(m.member_evidence(story, 'lmatsan'), [])

    def test_current_review_and_role_drift_remain_distinct(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]; pr['reviews'] = [self.review()]
        pr['declared_roles'] = dict(pr['declared_roles'], validation='lmatsan')
        gaps = m.role_gaps(story)
        self.assertFalse(any(g.startswith('Validacion, pruebas y documentacion:') for g in gaps))
        self.assertTrue(any('difieren' in g for g in gaps))

    def test_discussion_comment_is_attributed_but_not_a_validation_review(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr['comments'] = [{'url': 'comment-url', 'author': 'ParisArcos', 'date': '2026-09-07T12:00:00Z'}]
        self.assertEqual(m.member_evidence(story, 'ParisArcos'),
                         [('comentario de PR / 2026-09-07', 'comment-url')])
        self.assertTrue(any(g.startswith('Validacion, pruebas y documentacion:') for g in m.role_gaps(story)))
        self.assertEqual(m.member_evidence(story, 'lmatsan'), [])

    def test_unlinked_cards_remain_in_inventory(self):
        cards = [{'name': 'JUP-064 — Contribuciones', 'shortUrl': 'url', 'desc': ''},
                 {'name': 'Project information', 'shortUrl': 'other'}]
        snapshot = m.build_snapshot(cards, [], '2026-10-04')
        self.assertEqual(len(snapshot['stories']), 1)
        report = m.render(snapshot)
        self.assertIn('Pendiente de enlazar / no importado', report)
        self.assertIn('Liderazgo: identidad sin resolver', report)

    def test_coauthor_trailers_accept_name_alias_login_and_noreply(self):
        for trailer, login in [('Victor Mendez <v@example.com>', 'Victorh1397'),
                               ('Víctor Méndez <v@example.com>', 'Victorh1397'),
                               ('Paris Arcos <p@example.com>', 'ParisArcos'),
                               ('lmatsan <l@example.com>', 'lmatsan'),
                               ('LMATSAN <l@example.com>', 'lmatsan'),
                               ('Alias local <12345+Iber1to@users.noreply.github.com>', 'Iber1to'),
                               ('Alias local <iber1to@users.noreply.github.com>', 'Iber1to')]:
            self.assertEqual(m.declared_coauthors(f'feat: x\n\nCo-authored-by: {trailer}\n'), [login], trailer)
        for trailer in ['Lucia <lmatsan@example.com>', 'Assistant <noreply@example.com>',
                        'Lucia Mateo <1+Victorh1397@users.noreply.github.com>', 'Lucia Mateo Extra <l@example.com>',
                        'Alias <1+lmatsan@users.noreply.github.com.example.com>']:
            self.assertEqual(m.declared_coauthors(f'x\n\nCo-authored-by: {trailer}'), [], trailer)
        self.assertEqual(m.declared_coauthors('Thanks, co-authored-by: lmatsan <l@example.com>'), [])
        both = 'x\n\nCo-Authored-By: lmatsan <l@example.com>\n  co-authored-by: Paris Arcos Martin <p@example.com>'
        self.assertEqual(m.declared_coauthors(both), ['ParisArcos', 'lmatsan'])

    def test_author_threads_and_draft_reviews_are_not_review_actions(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr['reviews'] = [self.review(author='Victorh1397', state='COMMENTED', url='own-url'),
                         self.review(state='PENDING', url='draft-url'),
                         self.review(author='lmatsan', kinds={'JUP-064': 'other'}, head='old', url='untitled-url')]
        self.assertEqual(m.member_evidence(story, 'Victorh1397'),
                         [('PR publicada', pr['url']), ('intervencion del autor en su PR: COMMENTED', 'own-url')])
        self.assertEqual(m.member_evidence(story, 'ParisArcos'), [])
        self.assertEqual(m.member_evidence(story, 'lmatsan'),
                         [('review sin titulo: APPROVED / SHA anterior', 'untitled-url')])

    def test_report_uses_spanish_labels_for_internal_keys(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr.update(state='closed', draft=False, merged_at=None, checks=[], reviews=[self.review()],
                  artifacts=[{'kind': 'documentation', 'path': 'docs/a.md', 'url': 'doc-url'},
                             {'kind': 'tests', 'path': 'tools/tests/test_a.py', 'url': 'test-url'}])
        report = m.render({'captured_at': '2026-10-04', 'stories': [story]})
        for text in ['— cerrada sin integrar', '[validacion: APPROVED](review-url)',
                     '[documentacion: docs/a.md](doc-url)', '[pruebas: tools/tests/test_a.py](test-url)',
                     'Roles declarados en la PR: Liderazgo: Victor Mendez; Pairing/coautoria: Alejandro Aguado; '
                     'Revision de PR: Lucia Mateo; Validacion, pruebas y documentacion: Paris Arcos Martin.',
                     '- Revision de PR: sin evidencia estructurada actual de Lucia Mateo']:
            self.assertIn(text, report)
        for key in ['leadership', 'pairing:', 'review:', 'validation', 'other:', 'documentation', 'closed']:
            self.assertNotIn(key, report)
        pr.update(state='open')
        self.assertIn('— abierta', m.render({'captured_at': '2026-10-04', 'stories': [story]}))

    def test_collection_reads_trailers_and_never_stores_draft_reviews(self):
        pages = {'pulls/7': {'title': 'feat(JUP-064): x', 'head': {'ref': 'feat/JUP-064-x', 'sha': 'current'},
                             'html_url': 'pr-url', 'user': {'login': 'Victorh1397'}, 'state': 'open', 'draft': False,
                             'merged_at': None, 'body': '- Revision de PR: Lucia Mateo'},
                 'commits': [{'html_url': 'commit-url', 'sha': 'abc', 'author': None,
                              'commit': {'message': 'x\n\nCo-authored-by: Iber1to <a@example.com>'}}],
                 'reviews': [{'html_url': 'draft-url', 'user': {'login': 'lmatsan'}, 'state': 'PENDING',
                              'commit_id': 'current', 'submitted_at': None, 'body': 'Revision JUP-064'},
                             {'html_url': 'review-url', 'user': {'login': 'lmatsan'}, 'state': 'COMMENTED',
                              'commit_id': 'current', 'submitted_at': '2026-10-06T16:40:05Z',
                              'body': 'Revision JUP-064: ok'}],
                 'comments': [], 'files': []}

        def github(endpoint, paginate=False):
            return pages[endpoint] if endpoint in pages else pages[endpoint.split('/')[2].split('?')[0]]

        with mock.patch.object(m, 'github', github), mock.patch.object(m, 'run_json', return_value=[{'check_runs': []}]):
            pr = m.collect_pr({'number': 7})
        self.assertEqual(pr['commits'][0]['declared_coauthors'], ['Iber1to'])
        self.assertEqual([(r['url'], r['kinds']) for r in pr['reviews']], [('review-url', {'JUP-064': 'review'})])
        self.assertEqual(pr['declared_roles']['review'], 'lmatsan')

    def test_role_review_needs_another_person_a_current_state_and_the_title_of_the_role(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        for state, missing in [('APPROVED', False), ('COMMENTED', False), ('CHANGES_REQUESTED', True),
                               ('DISMISSED', True), ('PENDING', True)]:
            pr['reviews'] = [self.review(state=state)]
            self.assertEqual(self.missing(story, 'validation'), missing, state)
        pr['reviews'] = [self.review(author='lmatsan')]
        self.assertTrue(self.missing(story, 'review'))
        pr['reviews'] = [self.review(author='lmatsan', kinds={'JUP-065': 'review'})]
        self.assertTrue(self.missing(story, 'review'))
        pr['reviews'] = [self.review(author='lmatsan', kinds={'JUP-064': 'review'})]
        self.assertFalse(self.missing(story, 'review'))
        pr['author'] = 'lmatsan'
        self.assertTrue(self.missing(story, 'review'))

    def test_leadership_and_pairing_need_a_published_pr_a_commit_or_a_declared_coauthor(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        self.assertFalse(self.missing(story, 'leadership'))
        self.assertTrue(self.missing(story, 'pairing'))
        for commit in [{'author': 'Iber1to', 'declared_coauthors': []},
                       {'author': 'Victorh1397', 'declared_coauthors': ['Iber1to']}]:
            pr['commits'] = [dict(commit, url='commit-url')]
            self.assertFalse(self.missing(story, 'pairing'), commit)
        pr['commits'] = [{'url': 'commit-url', 'author': 'lmatsan', 'declared_coauthors': ['ParisArcos']}]
        self.assertTrue(self.missing(story, 'pairing'))
        pr['author'] = 'Iber1to'
        self.assertTrue(self.missing(story, 'leadership'))

    def test_pr_closed_without_merging_is_listed_but_is_not_current_role_evidence(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr.update(state='closed', draft=True, merged_at=None, checks=[], artifacts=[], reviews=[self.review()],
                  commits=[{'url': 'commit-url', 'author': 'Iber1to', 'declared_coauthors': []}])
        self.assertEqual([g.split(':')[0] for g in m.role_gaps(story)], list(m.ROLE_LABELS.values()))
        report = m.render({'captured_at': '2026-10-04', 'stories': [story]})
        self.assertIn('— cerrada sin integrar', report)
        self.assertIn('[PR publicada](https://github.com/example/pull/1)', report)
        self.assertIn('[commit](commit-url)', report)
        pr.update(merged_at='2026-10-05T00:00:00Z')
        self.assertEqual([g.split(':')[0] for g in m.role_gaps(story)], ['Revision de PR'])
        self.assertIn('— integrada', m.render({'captured_at': '2026-10-04', 'stories': [story]}))
        pr.update(state='open', merged_at=None)
        self.assertEqual([g.split(':')[0] for g in m.role_gaps(story)], ['Revision de PR'])
        self.assertIn('— borrador', m.render({'captured_at': '2026-10-04', 'stories': [story]}))

    def test_missing_role_key_and_deleted_account_do_not_break_the_report(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        del story['assigned_roles']['validation']
        pr.update(author=None, state='open', draft=False, merged_at=None, checks=[], artifacts=[],
                  reviews=[self.review(author=None)],
                  comments=[{'url': 'comment-url', 'author': None, 'date': '2026-09-07T12:00:00Z'}])
        report = m.render({'captured_at': '2026-10-04', 'stories': [story]})
        self.assertIn('- Validacion, pruebas y documentacion: identidad sin resolver', report)
        self.assertIn('Autor: `cuenta eliminada`', report)
        self.assertIn('| Paris Arcos Martin (`ParisArcos`) | 0 | 0 | 0 | 0 | 0 |', report)
        self.assertIn('| Lucia Mateo (`lmatsan`) | 0 | 0 | 0 | 1 | 0 |', report)
        self.assertNotIn('review-url', report)
        self.assertNotIn('comment-url', report)

    def test_requested_changes_follow_review_dates_not_list_order(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr['reviews'] = [self.review(state='APPROVED', date='2026-10-02T00:00:00Z'),
                         self.review(state='CHANGES_REQUESTED', date='2026-10-01T00:00:00Z')]
        self.assertFalse(any('cambios solicitados' in g for g in m.role_gaps(story)))
        pr['reviews'].append(self.review(author='lmatsan', state='CHANGES_REQUESTED', date='2026-10-03T00:00:00Z'))
        self.assertIn('PR #1: cambios solicitados pendientes', m.role_gaps(story))

    def test_report_caps_long_lists_and_points_to_the_snapshot(self):
        story = self.story(); pr = self.pr(); story['prs'] = [pr]
        pr.update(state='open', draft=False, merged_at=None,
                  checks=[{'name': 'CI', 'url': 'check-url', 'status': 'completed', 'conclusion': None}],
                  commits=[{'url': f'commit-{i}', 'author': 'Iber1to', 'declared_coauthors': []} for i in range(12)],
                  artifacts=[{'kind': 'documentation', 'path': f'docs/{name}', 'url': name}
                             for name in ['d.md', 'c.md', 'b.md', 'evidence/z.md']])
        snapshot = {'captured_at': '2026-10-04', 'stories': [story]}
        report = m.render(snapshot)
        self.assertIn('[commit](commit-11) |', report)
        self.assertNotIn('acciones adicionales', report)
        self.assertIn('- [documentacion: docs/evidence/z.md](evidence/z.md)\n- [documentacion: docs/b.md](b.md)\n'
                      '- [documentacion: docs/c.md](c.md)\n- [1 artefactos adicionales', report)
        self.assertNotIn('d.md', report)
        self.assertIn('- [CI](check-url): completed / pendiente', report)
        pr['commits'].append({'url': 'commit-12', 'author': 'Iber1to', 'declared_coauthors': []})
        report = m.render(snapshot)
        self.assertIn('[commit](commit-11)<br>[1 acciones adicionales en snapshot](JUP-064-snapshot.json) |', report)
        self.assertNotIn('commit-12', report)
        self.assertIn('| Alejandro Aguado (`Iber1to`) | 1 | 0 | 1 | 0 | 0 |', report)

    def test_snapshot_links_prs_by_identifier_and_sorts_stories(self):
        cards = [{'name': 'JUP-065 B', 'shortUrl': 'b'},
                 {'name': 'JUP-064 A', 'shortUrl': 'a', 'desc': '- Liderazgo: Victor Mendez\nTexto libre'},
                 {'name': 'JUP-0640 no', 'shortUrl': 'c'}, {'name': 'Nota JUP-064', 'shortUrl': 'd'}]
        prs = [{'number': 1, 'jups': ['JUP-064', 'JUP-065']}, {'number': 2, 'jups': ['JUP-065']}]
        snapshot = m.build_snapshot(cards, prs, 'now')
        self.assertEqual([(s['jup'], s['trello'], [p['number'] for p in s['prs']]) for s in snapshot['stories']],
                         [('JUP-064', 'a', [1]), ('JUP-065', 'b', [1, 2])])
        self.assertEqual(snapshot['stories'][0]['assigned_roles']['leadership'], 'Victorh1397')
        self.assertEqual(snapshot['stories'][0]['role_source_lines'], ['- Liderazgo: Victor Mendez'])
        self.assertEqual((snapshot['schema_version'], snapshot['captured_at'], snapshot['repository'], snapshot['team']),
                         (1, 'now', m.REPO, m.TEAM))

    def test_collection_survives_deleted_accounts_and_keeps_only_present_docs_and_tests(self):
        pr = self.collect(
            detail={'user': None, 'title': 'feat(JUP-065): x', 'head': {'ref': 'feat/JUP-064-JUP-065', 'sha': 'abc123'}},
            commits=[{'html_url': 'commit-url', 'sha': 'abc', 'author': {'login': 'victorh1397'}, 'commit': None},
                     {'html_url': 'other-url', 'sha': 'def', 'author': {'login': 'someone-else'},
                      'commit': {'message': None}}],
            reviews=[{'html_url': 'review-url', 'user': None, 'state': 'COMMENTED', 'commit_id': 'abc123',
                      'submitted_at': '2026-10-06T16:40:05Z', 'body': None}],
            comments=[{'html_url': 'comment-url', 'user': None, 'created_at': 'created', 'updated_at': 'updated'}],
            files=[{'filename': 'docs/a b.md', 'status': 'modified'}, {'filename': 'docs/gone.md', 'status': 'removed'},
                   {'filename': 'openspec/specs/x/spec.md', 'status': 'added'},
                   {'filename': 'apps/x/tests/test_a.py', 'status': 'added'}, {'filename': 'apps/x/main.py', 'status': 'modified'},
                   {'filename': 'apps/frontend/src/a.test.tsx', 'status': 'added'}, {'filename': 'apps/x/latest/a.py', 'status': 'added'}])
        self.assertEqual((pr['author'], pr['jups'], pr['head'], pr['state']), (None, ['JUP-064', 'JUP-065'], 'abc123', 'open'))
        self.assertEqual([(c['author'], c['declared_coauthors']) for c in pr['commits']],
                         [('Victorh1397', []), ('someone-else', [])])
        self.assertEqual([(r['author'], r['kinds']) for r in pr['reviews']],
                         [(None, {'JUP-064': 'other', 'JUP-065': 'other'})])
        self.assertEqual(pr['comments'], [{'url': 'comment-url', 'author': None, 'date': 'created', 'updated_at': 'updated'}])
        self.assertEqual([(a['path'], a['kind']) for a in pr['artifacts']],
                         [('docs/a b.md', 'documentation'), ('openspec/specs/x/spec.md', 'documentation'),
                          ('apps/x/tests/test_a.py', 'tests'), ('apps/frontend/src/a.test.tsx', 'tests')])
        self.assertEqual(pr['artifacts'][0]['url'], f'https://github.com/{m.REPO}/blob/abc123/docs/a%20b.md')

    def test_source_failure_shows_the_source_error_and_pages_are_flattened(self):
        done = lambda code, out='', err='': mock.Mock(returncode=code, stdout=out.encode('utf-8-sig'), stderr=err.encode())
        with mock.patch.object(m.subprocess, 'run', return_value=done(1, err='HTTP 502: Bad Gateway\n')):
            with self.assertRaisesRegex(RuntimeError, r'^gh api repos/\S+/pulls/7 exited 1: HTTP 502: Bad Gateway$'):
                m.github('pulls/7')
        with mock.patch.object(m.subprocess, 'run', return_value=done(0, '[[1, 2], [3]]')) as run:
            self.assertEqual(m.github('pulls?state=all', True), [1, 2, 3])
        self.assertEqual(run.call_args[0][0], ['gh', 'api', f'repos/{m.REPO}/pulls?state=all', '--paginate', '--slurp'])
        with mock.patch.object(m.subprocess, 'run', return_value=done(0, '{"cards": []}')) as run:
            self.assertEqual(m.run_json(['ssh', 'host'], 'código'), {'cards': []})
        self.assertEqual(run.call_args[1]['input'], 'código'.encode('utf-8'))

    def test_offline_render_rejects_foreign_snapshots_and_writes_the_same_bytes_everywhere(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot, output = Path(folder) / 'snapshot.json', Path(folder) / 'out' / 'register.md'
            good = m.build_snapshot([{'name': 'JUP-064 — Contribuciones', 'shortUrl': 'url', 'desc': ''}], [], '2026-10-04')
            for bad in [dict(good, schema_version=2), dict(good, team=dict(m.TEAM, lmatsan='Otra persona'))]:
                snapshot.write_text(json.dumps(bad), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.main('--snapshot', snapshot, '--output', output)
                self.assertFalse(output.exists())
            original = json.dumps(good)
            snapshot.write_text(original, encoding='utf-8')
            self.main('--snapshot', snapshot, '--output', output)
            self.assertEqual(output.read_bytes(), m.render(good).encode('utf-8'))
            self.assertEqual(snapshot.read_text(encoding='utf-8'), original)
            self.assertEqual(sorted(p.name for p in Path(folder).rglob('*') if p.is_file()), ['register.md', 'snapshot.json'])

    def test_collect_reads_trello_through_the_bridge_and_writes_only_a_complete_cut(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot, output = Path(folder) / 'snapshot.json', Path(folder) / 'register.md'
            snapshot.write_text('previous snapshot', encoding='utf-8')
            output.write_text('previous register', encoding='utf-8')
            cards = {'cards': [{'name': 'JUP-064 — Contribuciones', 'shortUrl': 'url', 'desc': ''}]}
            collected = lambda pr: dict(self.pr(), number=pr['number'], jups=['JUP-064'], state='open', draft=False,
                                        merged_at=None, artifacts=[], checks=[])
            arguments = ('--collect', '--snapshot', snapshot, '--output', output)
            with mock.patch.object(m, 'run_json', return_value=cards) as bridge, \
                    mock.patch.object(m, 'collect_pr', side_effect=collected):
                with mock.patch.object(m, 'github', side_effect=RuntimeError('gh failed')), self.assertRaises(RuntimeError):
                    self.main(*arguments)
                with mock.patch.object(m, 'github', return_value=[{'number': 7}]) as listing:
                    with mock.patch.object(m, 'render', side_effect=KeyError('broken')), self.assertRaises(KeyError):
                        self.main(*arguments)
                    self.assertEqual((snapshot.read_text(encoding='utf-8'), output.read_text(encoding='utf-8')),
                                     ('previous snapshot', 'previous register'))
                    self.main(*arguments)
            written = json.loads(snapshot.read_text(encoding='utf-8'))
            self.assertEqual([p['number'] for p in written['stories'][0]['prs']], [7])
            self.assertEqual((written['schema_version'], written['team']), (1, m.TEAM))
            self.assertEqual(output.read_bytes(), m.render(written).encode('utf-8'))
            self.assertTrue(snapshot.read_bytes().endswith(b'}\n'))
            self.assertNotIn(b'\r', snapshot.read_bytes())
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()), ['register.md', 'snapshot.json'])
            self.assertEqual(listing.call_args[0], ('pulls?state=all&per_page=100', True))
            command, script = bridge.call_args[0]
            self.assertEqual(command[:4], ['ssh', '-o', 'ConnectTimeout=15', 'DockerServer'])
            self.assertEqual(m.re.findall(r'\bc\.(\w+)\(', script), ['get_cards'])

    def test_interrupted_write_keeps_the_previous_file(self):
        def interrupted(self, text, **kwargs):
            self.write_bytes(b'half written')
            raise OSError('disk full')

        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'register.md'
            output.write_bytes(b'previous register')
            with mock.patch.object(Path, 'write_text', interrupted), self.assertRaises(OSError):
                m.write_atomic(output, 'new register')
            self.assertEqual(output.read_bytes(), b'previous register')


class VersionedContributionReportTests(unittest.TestCase):
    def test_versioned_report_matches_versioned_snapshot(self):
        root = Path(__file__).resolve().parents[2]
        import json
        snapshot = json.loads((root / 'docs/contributions/JUP-064-snapshot.json').read_text(encoding='utf-8'))
        report = (root / 'docs/contributions/JUP-064-register.md').read_text(encoding='utf-8')
        self.assertEqual(m.render(snapshot), report,
                         'Regenerate the versioned report whenever the snapshot or renderer changes')


if __name__ == '__main__':
    unittest.main()
