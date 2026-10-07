import importlib.util
from pathlib import Path
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


if __name__ == '__main__':
    unittest.main()
