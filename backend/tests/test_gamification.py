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
