import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import date
from werkzeug.exceptions import NotFound
from flask import session

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

import os

os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("ADMIN_PASSWORD", "test-only-password")

import app as flask_app


class FakeCursor:
    def __init__(self):
        self.rowcount = 1
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        return (
            "Old Name", date(1950, 1, 1), "Female", "Widowed",
            "Spouse Name", "Employer", "Old Address", "Old Village",
            "Post Office", "Block", "District", "State", "495001",
            "1234567890", "ABCD0123456", "PENDING"
        )

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        pass


class EditApplicationTest(unittest.TestCase):
    def test_citizen_can_update_own_pending_application(self):
        connection = FakeConnection()

        with flask_app.app.test_request_context(
            "/edit_application/1",
            method="POST",
            data={
                "applicant_name": "Updated Name",
                "dob": "01/01/1950",
                "gender": "Female",
                "marital_status": "Widowed",
                "spouse_name": "Spouse Name",
                "spouse_employer": "Employer",
                "full_address": "New Address",
                "village": "New Village",
                "post_office": "Post Office",
                "block": "Block",
                "district": "District",
                "state": "State",
                "pin_code": "495001",
                "bank_account": "1234567890",
                "ifsc": "abcd0123456",
            },
        ):
            session["logged_in"] = True
            session["portal_mobile"] = "2222222222"

            with patch.object(
                flask_app, "get_db", return_value=connection
            ):
                response = flask_app.edit_application(1)

        update_queries = [
            query for query, params in connection.fake_cursor.queries
            if query.strip().upper().startswith("UPDATE APPLICATIONS")
        ]

        self.assertEqual(len(update_queries), 1)
        self.assertTrue(connection.committed)
        self.assertEqual(response.status_code, 302)
        
    def test_citizen_cannot_edit_another_citizens_application(self):
        connection = FakeConnection()

        connection.fake_cursor.fetchone = lambda: None

        with flask_app.app.test_request_context("/edit_application/1"):
            session["logged_in"] = True
            session["portal_mobile"] = "1111111111"

            with patch.object(
                flask_app, "get_db", return_value=connection
            ):
                with self.assertRaises(NotFound):
                    flask_app.edit_application(1)


if __name__ == "__main__":
    unittest.main()