import unittest
from pathlib import Path


class SchedulerConfigTest(unittest.TestCase):
    def test_scheduler_uses_existing_config_file(self):
        project_root = Path(__file__).resolve().parents[1]
        script = project_root / "app" / "scripts" / "deemed_approval.py"

        source = script.read_text()

        self.assertIn('"app.ini"', source)

        config_file = project_root / "app" / "config" / "app.ini"
        self.assertTrue(config_file.exists())
        
    def test_dockerfile_starts_cron_service(self):
        project_root = Path(__file__).resolve().parents[1]
        dockerfile = project_root / "app" / "Dockerfile"

        source = dockerfile.read_text()

        self.assertIn("cron", source.lower())
        self.assertRegex(source, r"(service cron start|cron -f)")


if __name__ == "__main__":
    unittest.main()
