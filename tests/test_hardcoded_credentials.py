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


if __name__ == "__main__":
    unittest.main()

