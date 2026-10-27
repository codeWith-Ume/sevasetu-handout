import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import session
from werkzeug.exceptions import NotFound

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("ADMIN_PASSWORD", "test-only-password")

import app as flask_app


class FakeCursor:
    def execute(self, query, params=None):
        pass

    def fetchone(self):
        return (
            "APP-001",
            "Citizen B",
            "2222222222",
            None, None, None, None, None, "PENDING", None, None
        )

    def close(self):
        pass


class FakeConnection:
    def cursor(self):
        return FakeCursor()

    def close(self):
        pass


class ApplicationPrivacyTest(unittest.TestCase):
    def test_citizen_cannot_view_another_citizens_application(self):
        with flask_app.app.test_request_context("/application/1"):
            session["logged_in"] = True
            session["portal_mobile"] = "1111111111"

            with patch.object(
                flask_app, "get_db", return_value=FakeConnection()
            ):
                with self.assertRaises(NotFound):
                    flask_app.view_application(1)


if __name__ == "__main__":
    unittest.main()
