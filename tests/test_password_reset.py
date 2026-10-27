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
    def test_password_reset_requires_otp_verification(self):
        start = self.source.index("def reset_password():")
        end = self.source.find("\n@app.route", start + 1)
        reset_function = self.source[start:end]

        self.assertIn(
            "session.get(",
            reset_function,
            "Password reset must check a verified session."
        )
    def test_password_hashing_uses_werkzeug(self):
        self.assertIn(
            "generate_password_hash",
            self.source,
            "Passwords should use Werkzeug's secure password hashing."
        )
        self.assertIn(
            "check_password_hash",
            self.source,
            "Login should verify Werkzeug password hashes."
        )

    def test_edit_application_does_not_reset_password_to_dob(self):
        start = self.source.index('def edit_application(')
        end = self.source.find('\n@app.route', start + 1)
        edit_function = self.source[start:end]

        self.assertNotIn(
            'UPDATE portal_users SET password_hash = %s WHERE mobile = %s',
            edit_function,
            "Editing an application must not reset the portal password."
        )
        self.assertNotIn(
            'hash_password(dob.strftime("%d%m%Y"))',
            edit_function,
            "DOB must not be used as the password during application editing."
        )

if __name__ == "__main__":
    unittest.main()
