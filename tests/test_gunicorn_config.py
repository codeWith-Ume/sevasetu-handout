import unittest
from pathlib import Path


class GunicornConfigTest(unittest.TestCase):
    def test_gunicorn_uses_threaded_workers(self):
        root = Path(__file__).resolve().parents[1]
        dockerfile = (root / "app" / "Dockerfile").read_text()

        self.assertIn('"--worker-class", "gthread"', dockerfile)
        self.assertIn('"--threads", "2"', dockerfile)


if __name__ == "__main__":
    unittest.main()
