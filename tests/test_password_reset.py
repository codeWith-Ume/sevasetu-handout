import unittest
from pathlib import Path


class PasswordResetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_path = Path(__file__).parents[1] / "app" / "app.py"
        cls.source = app_path.read_text()

    def test_password_reset_does_not_use_dob_as_password(self):
        start = self.source.index("def reset_password():")
        end = self.source.find("\n@app.route", start + 1)
        reset_function = self.source[start:end]

        self.assertNotIn(
            'newpass = r2[0].strftime("%d%m%Y")',
            reset_function,
            "Password reset must not use DOB as the password."
        )

    def test_password_reset_requires_more_than_mobile_number(self):
        start = self.source.index("def reset_password():")
        end = self.source.find("\n@app.route", start + 1)
        reset_function = self.source[start:end]

        self.assertNotIn(
            'cur.execute("UPDATE portal_users SET password_hash = %s WHERE mobile = %s"',
            reset_function,
            "Password must not reset from mobile number alone."
        )
    def test_login_uses_secure_password_verification(self):
        start = self.source.index('def status_login():')
        end = self.source.find('\n@app.route', start + 1)
        login_function = self.source[start:end]

        self.assertNotIn(
            'row[0] == hash_password(password)',
            login_function,
            "Login should use a secure password verification method."
        )


if __name__ == "__main__":
    unittest.main()
