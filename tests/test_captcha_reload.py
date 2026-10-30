import os
import sys
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("ADMIN_PASSWORD", "test-only-password")

import app as flask_app
def test_reload_captcha_generates_new_answer_and_timestamp():
    client = flask_app.app.test_client()

    with client.session_transaction() as sess:
        sess["captcha_answer"] = "OLD123"
        sess["captcha_created_at"] = 100

    response = client.get("/captcha-reload")

    assert response.status_code == 200
    assert response.get_json() == {"success": True}

    with client.session_transaction() as sess:
        assert sess["captcha_answer"] != "OLD123"
        assert len(sess["captcha_answer"]) == 6
        assert "captcha_created_at" in sess