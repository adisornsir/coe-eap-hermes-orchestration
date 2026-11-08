import unittest
from demo_app.health import status

class HealthTests(unittest.TestCase):
    def test_status(self):
        self.assertEqual(status(), {"status": "ok"})
