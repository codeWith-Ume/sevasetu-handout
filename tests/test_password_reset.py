import unittest
from pathlib import Path


class PasswordResetTest(unittest.TestCase):
    def test_password_reset_does_not_use_dob_as_password(self):
        app_path = Path(__file__).parents[1] / "app" / "app.py"
        source = app_path.read_text()

        start = source.index("def reset_password():")
        end = source.find("\n@app.route", start + 1)
        reset_function = source[start:end]

        self.assertNotIn(
            'newpass = r2[0].strftime("%d%m%Y")',
            reset_function,
            "Password reset should not use date of birth as the password."
        )


if __name__ == "__main__":
    unittest.main()
