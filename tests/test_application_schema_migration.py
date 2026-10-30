import unittest
from pathlib import Path


class ApplicationSchemaMigrationTest(unittest.TestCase):
    def test_migration_adds_missing_application_columns_safely(self):
        project_root = Path(__file__).resolve().parents[1]
        migration = (
            project_root
            / "app"
            / "migrations"
            / "20261031_add_missing_application_columns.sql"
        )

        self.assertTrue(migration.exists(), "Application migration file is missing")

        sql = migration.read_text().lower()

        for column in ("guardian_name", "account_holder_name"):
            self.assertRegex(
                sql,
                rf"add\s+column\s+if\s+not\s+exists\s+{column}\b",
            )


if __name__ == "__main__":
    unittest.main()
