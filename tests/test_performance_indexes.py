import unittest
from pathlib import Path


class PerformanceIndexesTest(unittest.TestCase):
    def test_applications_has_dashboard_performance_index(self):
        project_root = Path(__file__).resolve().parents[1]
        schema = (project_root / "app" / "schema.sql").read_text().lower()

        self.assertRegex(
            schema,
            r"create\s+index[^;]*\bon\s+applications\s*\([^;]*(status|submitted_at)"
        )


if __name__ == "__main__":
    unittest.main()
