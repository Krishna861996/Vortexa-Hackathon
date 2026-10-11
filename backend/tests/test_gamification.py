import unittest
from fastapi.testclient import TestClient
from tests.test_api import FakeRepository
from app.main import app
from app.repository import get_repository
from app.auth import optional_identity
from tests.test_api import TEST_IDENTITY


class PracticeRepository(FakeRepository):
    def __init__(self):
        super().__init__()
        self.library = [dict(self.challenge, id=id, difficulty=level) for id, level in [('start', 'beginner'), ('easy-a', 'easy'), ('easy-b', 'easy'), ('medium', 'medium')]]

    def list_challenges(self):
        return self.library

    def get_challenge(self, id):
        return next((row for row in self.library if row['id'] == id), None)


class GamificationTests(unittest.TestCase):
    def setUp(self):
        self.repo = PracticeRepository()
        app.dependency_overrides[get_repository] = lambda: self.repo
        app.dependency_overrides[optional_identity] = lambda: TEST_IDENTITY
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def submit(self, id, category='passed'):
        return self.client.post(f'/api/challenges/{id}/practice-attempts', json={'code':'def add_numbers(a,b): return a+b', 'categories':[category]})

    def test_unlocks_require_all_challenges_and_persist(self):
        self.assertEqual(self.submit('easy-a').status_code, 403)
        self.submit('start', 'wrong output')
        self.assertTrue(self.client.get('/api/challenges/easy-a').json()['locked'])
        response = self.submit('start')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['execution'], 'browser')
        self.assertFalse(self.client.get('/api/challenges/easy-a').json()['locked'])
        self.submit('easy-a')
        self.assertTrue(self.client.get('/api/challenges/medium').json()['locked'])
        self.submit('easy-b')
        self.assertFalse(self.client.get('/api/challenges/medium').json()['locked'])
        self.assertEqual(self.client.get('/api/learners/demo-learner/progress').json()['solved_challenges'], 3)

    def test_invalid_results_are_not_saved(self):
        response = self.client.post('/api/challenges/start/practice-attempts', json={'code':'pass','categories':['passed','passed']})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.repo.attempts, [])

    def test_locked_mentor_and_hints(self):
        self.assertEqual(self.client.post('/api/challenges/easy-a/hints/next', json={}).status_code, 403)
        self.assertEqual(self.client.post('/api/challenges/easy-a/mentor', json={'question':'Help'}).status_code, 403)

    def test_xp_rewards_independence_more_than_hints(self):
        # 1. Independent solver (0 hints revealed):
        # Base XP for beginner is 100, plus 50 Solo Maverick bonus = 150 XP!
        res_solo = self.submit('start', 'passed')
        self.assertEqual(res_solo.status_code, 200)
        data_solo = res_solo.json()
        self.assertTrue(data_solo['solo_bonus'])
        self.assertEqual(data_solo['hints_used'], 0)
        self.assertEqual(data_solo['stars'], 3)
        self.assertGreaterEqual(data_solo['earned_xp'], 150)

        # 2. Solver who requested hints:
        # Request 1 hint on easy-a first
        hint_res = self.client.post('/api/challenges/easy-a/hints/next', json={})
        self.assertEqual(hint_res.status_code, 200)

        # Submit easy-a
        res_hinted = self.submit('easy-a', 'passed')
        self.assertEqual(res_hinted.status_code, 200)
        data_hinted = res_hinted.json()
        self.assertFalse(data_hinted['solo_bonus'])
        self.assertEqual(data_hinted['hints_used'], 1)
        self.assertEqual(data_hinted['stars'], 2)
        # Verify unique twist: 0 hints earns more than with hints!
        self.assertLess(data_hinted['earned_xp'], data_solo['earned_xp'])

    def test_badges_and_progress_map(self):
        self.submit('start', 'passed')
        progress = self.client.get('/api/learners/demo-learner/progress').json()
        self.assertIn('total_xp', progress)
        self.assertGreater(progress['total_xp'], 0)
        self.assertIn('current_level', progress)
        self.assertIn('level_name', progress)
        self.assertIn('badges', progress)
        self.assertIn('progress_map', progress)
        
        # Check unlocked badges
        unlocked_badge_ids = [b['id'] for b in progress['badges'] if b['unlocked']]
        self.assertIn('first_mission', unlocked_badge_ids)
        self.assertIn('solo_maverick', unlocked_badge_ids)

        # Check progress map nodes
        self.assertGreater(len(progress['progress_map']), 0)
        start_node = next(n for n in progress['progress_map'] if n['challenge_id'] == 'start')
        self.assertEqual(start_node['status'], 'completed')
        self.assertEqual(start_node['stars'], 3)

    def test_diff_analyzer_explains_division_vs_modulo_modification(self):
        before = "def is_even(n):\n    if (n / 2 == 0):\n        return True\n    return False"
        after = "def is_even(n):\n    if (n % 2 == 0):\n        return True\n    return False"
        res = self.client.post('/api/challenges/start/analyze-diff', json={'before_code': before, 'after_code': after})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('diff_hunks', data)
        self.assertIn('explanations', data)
        self.assertIn('why_it_helps', data)
        # Check specific educational explanations
        full_text = " ".join(data['explanations'])
        self.assertIn("division", full_text)
        self.assertIn("remainder", full_text)
        self.assertIn("zero", full_text)

    def test_list_challenge_attempts_preserves_history(self):
        self.submit('start', 'wrong output')
        self.submit('start', 'passed')
        res = self.client.get('/api/challenges/start/attempts')
        self.assertEqual(res.status_code, 200)
        attempts = res.json()
        self.assertEqual(len(attempts), 2)
        # Most recent attempt is first
        self.assertTrue(attempts[0]['passed'])
        self.assertFalse(attempts[1]['passed'])


