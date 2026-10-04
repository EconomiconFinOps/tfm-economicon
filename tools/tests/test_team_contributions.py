import importlib.util
from pathlib import Path
import unittest

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

    def test_title_must_match_story_and_entire_first_line(self):
        self.assertEqual(m.review_kind('Validación JUP-064\nEvidence', 'JUP-064'), 'validation')
        for text in ['Validacion JUP-065', 'I did Validacion JUP-064', 'Validacion JUP-0640', '# Validacion JUP-064']:
            self.assertEqual(m.review_kind(text, 'JUP-064'), 'other')

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
            self.assertTrue(any(g.startswith('validation:') for g in m.role_gaps(story)))

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
        self.assertFalse(any(g.startswith('validation:') for g in gaps))
        self.assertTrue(any('difieren' in g for g in gaps))

    def test_unlinked_cards_remain_in_inventory(self):
        cards = [{'name': 'JUP-064 — Contribuciones', 'shortUrl': 'url', 'desc': ''},
                 {'name': 'Project information', 'shortUrl': 'other'}]
        snapshot = m.build_snapshot(cards, [], '2026-10-04')
        self.assertEqual(len(snapshot['stories']), 1)
        report = m.render(snapshot)
        self.assertIn('Pendiente de enlazar / no importado', report)
        self.assertIn('leadership: identidad sin resolver', report)


if __name__ == '__main__':
    unittest.main()
