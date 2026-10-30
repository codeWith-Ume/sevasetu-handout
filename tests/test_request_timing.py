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
