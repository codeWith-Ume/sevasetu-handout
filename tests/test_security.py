import ast
import unittest
from pathlib import Path


class PasswordResetSecurityTest(unittest.TestCase):
    def test_password_reset_uses_parameterized_sql(self):
        source_path = Path(__file__).resolve().parents[1] / "app" / "app.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        reset_function = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "reset_password"
        )

        execute_calls = [
            node for node in ast.walk(reset_function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "execute"
        ]

        mobile_queries = [
            call for call in execute_calls
            if call.args
            and isinstance(call.args[0], (ast.Constant, ast.JoinedStr, ast.BinOp))
            and "mobile" in ast.unparse(call.args[0]).lower()
        ]

        self.assertGreaterEqual(
            len(mobile_queries), 2,
            "Expected both mobile-number queries in password reset."
        )

        for call in mobile_queries:
            with self.subTest(query=ast.unparse(call.args[0])):
                self.assertGreaterEqual(
                    len(call.args), 2,
                    "SQL must use a query parameter instead of joining user input."
                )
                self.assertIsInstance(
                    call.args[0], ast.Constant,
                    "SQL query must be a fixed string."
                )
                self.assertIn(
                    "%s", call.args[0].value,
                    "SQL query must use a parameter placeholder."
                )
    def test_only_admin_can_approve_or_reject(self):
        source_path = Path(__file__).resolve().parents[1] / "app" / "app.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))

        protected_routes = {"admin_approve", "admin_reject"}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in protected_routes:
                with self.subTest(route=node.name):
                    source = ast.unparse(node)
                    self.assertIn(
                        "session.get('admin')",
                        source,
                        f"{node.name} must check admin permission."
                    )


if __name__ == "__main__":
    unittest.main()
