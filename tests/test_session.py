"""Tests for session persistence (save_session / load_session)."""

from pathlib import Path
import tempfile
import unittest

from fi.client import FiClient
from fi.transport import FiTransport


class TestSessionPersistence(unittest.TestCase):
    def test_save_and_load_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "test_session.json"

            transport1 = FiTransport()
            transport1.set_session(
                session_id="mock_session_12345",
                user_id="user_abc_789",
                email="doglover@example.com",
            )
            self.assertTrue(transport1.is_authenticated)

            transport1.save_session(session_path)
            self.assertTrue(session_path.exists())

            # Create a brand new transport and load the saved session
            transport2 = FiTransport()
            self.assertFalse(transport2.is_authenticated)

            loaded = transport2.load_session(session_path)
            self.assertTrue(loaded)
            self.assertTrue(transport2.is_authenticated)
            self.assertEqual(transport2.session_id, "mock_session_12345")
            self.assertEqual(transport2.user_id, "user_abc_789")
            self.assertEqual(transport2.email, "doglover@example.com")

            # Check that cookiejar contains the restored cookies
            cookie_names = [c.name for c in transport2.cookie_jar]
            self.assertIn("fi.sid", cookie_names)
            self.assertIn("fi_session_id", cookie_names)

    def test_client_auto_load_session(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session_path = Path(tmpdir) / "client_session.json"

            # Create and save a session
            client1 = FiClient()
            client1.transport.set_session(
                session_id="session_xyz",
                user_id="user_xyz",
                email="alex@example.com",
            )
            client1.save_session(session_path)

            # Initialize a new client with session_file pointing to saved session
            client2 = FiClient(session_file=session_path)
            self.assertTrue(client2.is_authenticated)
            self.assertEqual(client2.current_user_id, "user_xyz")


if __name__ == "__main__":
    unittest.main()
