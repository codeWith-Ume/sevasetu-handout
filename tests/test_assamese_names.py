import os
import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("ADMIN_PASSWORD", "test-only-password")

import app as flask_app


class AssameseNameTest(unittest.TestCase):
    def test_assamese_name_is_preserved_by_sanitize(self):
        assamese_name = "প্ৰিয়ংকা দাস"
        result = flask_app.sanitize(assamese_name)

        self.assertEqual(
            result,
            assamese_name,
            "Assamese characters should be preserved in applicant names."
        )
    def test_assamese_name_is_not_truncated_by_character_limit(self):
        assamese_name = "প্ৰিয়ংকা দাস"
        result = flask_app.sanitize(assamese_name, maxlen=100)
        self.assertEqual(result, assamese_name)

if __name__ == "__main__":
    unittest.main()
