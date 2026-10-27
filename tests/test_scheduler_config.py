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
        
    def test_scheduler_service_starts_cron(self):
        project_root = Path(__file__).resolve().parents[1]
        compose_file = project_root / "docker-compose.yml"

        source = compose_file.read_text()

        self.assertRegex(
            source,
            r"(?s)scheduler:\s.*?command:\s*\[\"cron\",\s*\"-f\"\]"
        )


if __name__ == "__main__":
    unittest.main()
