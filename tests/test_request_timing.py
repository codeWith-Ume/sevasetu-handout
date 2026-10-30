import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("ADMIN_PASSWORD", "test-only-password")

import app as flask_app


def test_send_sms_logs_duration(caplog):
    with patch.object(flask_app.requests, "post") as mock_post:
        mock_post.return_value.status_code = 200

        with caplog.at_level(logging.INFO, logger=flask_app.app.logger.name):
            flask_app.send_sms("1234567890", "test message")

    assert "SMS request duration" in caplog.text


def test_acknowledgment_pdf_logs_duration(caplog):
    from datetime import date, datetime
    import logging

    class FakeCursor:
        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return (
                "SSP26123456", "Test Applicant", "1234567890",
                date(1950, 1, 1), "Test Village", "Test Block",
                "123456789012", "ABCD0123456",
                datetime(2026, 10, 30, 10, 0), "PENDING",
            )

    with caplog.at_level(
        logging.INFO, logger=flask_app.app.logger.name
    ):
        pdf_bytes = flask_app.generate_acknowledgment(FakeCursor(), 1)

    assert pdf_bytes
    assert "PDF generation duration" in caplog.text
