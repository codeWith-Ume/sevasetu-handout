import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class DeemedApprovalTest(unittest.TestCase):

    @patch("app.scripts.deemed_approval.requests.post")
    @patch("app.scripts.deemed_approval.psycopg2.connect")
    def test_overdue_applications_are_approved(
        self, mock_connect, mock_post
    ):
        from app.scripts import deemed_approval

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            ("TEST-APP-001", "9999999999")
        ]

        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test"}):
            deemed_approval.main()

        sql = mock_cursor.execute.call_args[0][0]

        self.assertIn("status = 'DEEMED_APPROVED'", sql)
        self.assertIn("status = 'PENDING'", sql)
        self.assertIn("submitted_at < %s", sql)
        mock_conn.commit.assert_called_once()
        mock_post.assert_called_once()
        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()