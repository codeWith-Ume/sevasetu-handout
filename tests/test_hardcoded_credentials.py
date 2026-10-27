import configparser
import unittest
from pathlib import Path


class HardcodedCredentialsTest(unittest.TestCase):
    def test_config_does_not_store_database_password(self):
        config_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "config"
            / "app.ini"
        )

        config = configparser.ConfigParser()
        config.read(config_path)

        self.assertNotIn("password", config["database"])

    def test_config_does_not_store_secret_key(self):
        config_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "config"
            / "app.ini"
        )

        config = configparser.ConfigParser()
        config.read(config_path)

        self.assertNotIn("secret_key", config["app"])
    def test_docker_database_password_uses_environment_variable(self):
        project_root = Path(__file__).resolve().parents[1]
        compose_file = project_root / "docker-compose.yml"
        compose_text = compose_file.read_text()

        self.assertRegex(
            compose_text,
            r"POSTGRES_PASSWORD:\s*\$\{POSTGRES_PASSWORD"
        )


if __name__ == "__main__":
    unittest.main()

