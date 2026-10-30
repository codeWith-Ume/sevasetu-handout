from pathlib import Path


def test_gunicorn_uses_threaded_workers():
    dockerfile = Path("app/Dockerfile").read_text()

    assert '"--worker-class", "gthread"' in dockerfile
    assert '"--threads", "2"' in dockerfile
