import unittest
from pathlib import Path


class SchedulerConfigTest(unittest.TestCase):
    def test_scheduler_config_file_exists(self):
        project_root = Path(__file__).resolve().parents[1]
        config_file = project_root / "app" / "config" / "settings.ini"

        self.assertTrue(
            config_file.exists(),
            f"Scheduler config file missing: {config_file}"
        )


if __name__ == "__main__":
    unittest.main()
