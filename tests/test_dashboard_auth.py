import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from dashboard import server as dashboard_server
    _READY = dashboard_server._DEPS_OK
except Exception:                                    # fastapi / httpx not installed
    _READY = False


class LoginThrottleTests(unittest.TestCase):
    def setUp(self):
        if not _READY:
            self.skipTest("fastapi and httpx are required for dashboard tests")
        self.now = 1000.0
        self.throttle = dashboard_server.LoginThrottle(
            max_failures=3, window=60.0, clock=lambda: self.now)

    def test_blocks_after_the_limit_and_recovers_when_the_window_passes(self):
        for _ in range(3):
            self.assertEqual(self.throttle.retry_after("phone"), 0)
            self.throttle.fail("phone")

        self.assertEqual(self.throttle.retry_after("phone"), 61)
        self.assertEqual(self.throttle.retry_after("laptop"), 0)

        self.now += 30
        self.assertEqual(self.throttle.retry_after("phone"), 31)
        self.now += 31
        self.assertEqual(self.throttle.retry_after("phone"), 0)

    def test_a_successful_login_clears_earlier_failures(self):
        self.throttle.fail("phone")
        self.throttle.fail("phone")
        self.throttle.succeed("phone")
        self.throttle.fail("phone")

        self.assertEqual(self.throttle.retry_after("phone"), 0)


class DashboardAuthTests(unittest.TestCase):
    def setUp(self):
        if not _READY:
            self.skipTest("fastapi and httpx are required for dashboard tests")
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.server = dashboard_server.DashboardServer()
        self.server._uploads_dir = Path(self._tmp.name)
        self.server.set_control_callback(lambda action: {"ok": True, "state": action})
        self.client = TestClient(self.server.app)
        self.addCleanup(self.client.close)

    def _login(self) -> dict:
        key = self.server.new_key()
        response = self.client.post("/login", json={"pin": key.lower()})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['token']}"}

    def test_pairing_key_works_once_and_authorises_commands(self):
        key = self.server.new_key()

        first = self.client.post("/login", json={"pin": key})
        second = self.client.post("/login", json={"pin": key})

        self.assertTrue(first.json()["ok"])
        self.assertEqual(second.status_code, 401)

        headers = {"Authorization": f"Bearer {first.json()['token']}"}
        sent = self.client.post("/api/command", json={"text": " open notepad "},
                                headers=headers)
        self.assertEqual(sent.status_code, 200)
        self.assertEqual(self.server._command_queue.get_nowait(), "open notepad")

    def test_protected_endpoints_reject_missing_and_invalid_tokens(self):
        for headers in ({}, {"Authorization": "Bearer not-a-real-token"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.client.post(
                    "/api/command", json={"text": "hi"}, headers=headers).status_code, 401)
                self.assertEqual(self.client.post(
                    "/api/wake", headers=headers).status_code, 401)
                self.assertEqual(self.client.get(
                    "/api/files", headers=headers).status_code, 401)
                self.assertEqual(self.client.post(
                    "/api/revoke-devices", headers=headers).status_code, 401)
        self.assertEqual(self.client.get("/uploads/x.txt?token=nope").status_code, 401)
        self.assertTrue(self.server._command_queue.empty())

    def test_repeated_wrong_keys_lock_the_address_out(self):
        real_key = self.server.new_key()
        limit = dashboard_server.LOGIN_MAX_FAILURES

        for _ in range(limit):
            self.assertEqual(
                self.client.post("/login", json={"pin": "WRONG1"}).status_code, 401)

        blocked = self.client.post("/login", json={"pin": real_key})
        self.assertEqual(blocked.status_code, 429)
        self.assertGreater(int(blocked.headers["Retry-After"]), 0)
        self.assertEqual(self.client.post(
            "/api/qr-login", json={"key": real_key, "request_id": "r1"}).status_code, 429)
        # The real key was not consumed by the blocked attempt.
        self.assertIn(real_key, self.server._pending_keys)

    def test_malformed_bodies_are_rejected_without_a_server_error(self):
        headers = self._login()
        for body in ("not json", "[1, 2]", '"text"', "null"):
            with self.subTest(body=body):
                raw = {"content": body, "headers": {"Content-Type": "application/json"}}
                self.assertEqual(self.client.post("/login", **raw).status_code, 400)
                self.assertEqual(self.client.post("/api/qr-login", **raw).status_code, 400)
                self.assertEqual(self.client.post("/api/device-login", **raw).status_code, 400)
                authed = {"content": body,
                          "headers": {"Content-Type": "application/json", **headers}}
                self.assertEqual(self.client.post("/api/command", **authed).status_code, 400)
                self.assertEqual(self.client.post("/api/control", **authed).status_code, 400)
        self.assertEqual(self.client.post(
            "/login", json={"pin": ["A", "B"]}).status_code, 401)

    def test_oversized_commands_are_refused(self):
        headers = self._login()
        too_long = "x" * (dashboard_server.MAX_COMMAND_CHARS + 1)

        response = self.client.post("/api/command", json={"text": too_long}, headers=headers)

        self.assertEqual(response.status_code, 413)
        self.assertTrue(self.server._command_queue.empty())

    def test_qr_login_is_idempotent_for_the_same_browser_only(self):
        key = self.server.new_key()

        first = self.client.post("/api/qr-login", json={"key": key, "request_id": "abc"})
        retry = self.client.post("/api/qr-login", json={"key": key, "request_id": "abc"})
        other = self.client.post("/api/qr-login", json={"key": key, "request_id": "zzz"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(retry.json(), first.json())
        self.assertEqual(other.status_code, 401)

        again = self.client.post("/api/device-login",
                                 json={"device_token": first.json()["device_token"]})
        self.assertTrue(again.json()["ok"])
        self.assertEqual(self.client.post(
            "/api/device-login", json={"device_token": "unknown"}).status_code, 401)

    def test_stale_device_tokens_do_not_count_against_pairing(self):
        for _ in range(dashboard_server.LOGIN_MAX_FAILURES + 2):
            self.client.post("/api/device-login", json={"device_token": "stale"})

        key = self.server.new_key()
        self.assertEqual(self.client.post("/login", json={"pin": key}).status_code, 200)

    def test_oldest_sessions_are_dropped_once_the_table_is_full(self):
        first = self.server._issue_token("KEY001")
        for index in range(dashboard_server.MAX_SESSIONS):
            self.server._issue_token(f"K{index:05d}")

        self.assertNotIn(first, self.server._tokens)
        self.assertEqual(len(self.server._tokens), dashboard_server.MAX_SESSIONS)
        self.assertEqual(set(self.server._token_keys), self.server._tokens)

    def test_downloads_cannot_leave_the_uploads_folder(self):
        headers = self._login()
        token = headers["Authorization"].removeprefix("Bearer ")
        (Path(self._tmp.name) / "note.txt").write_text("hello", encoding="utf-8")
        secret = Path(self._tmp.name).parent / "outside-secret.txt"
        secret.write_text("private", encoding="utf-8")
        self.addCleanup(secret.unlink)

        ok = self.client.get(f"/uploads/note.txt?token={token}")
        self.assertEqual(ok.text, "hello")
        for name in ("..%2Foutside-secret.txt", "..%5Coutside-secret.txt",
                     "%2E%2E%2Foutside-secret.txt"):
            with self.subTest(name=name):
                response = self.client.get(f"/uploads/{name}?token={token}")
                self.assertNotEqual(response.status_code, 200)
                self.assertNotIn("private", response.text)

    def test_uploaded_names_are_flattened_and_never_overwrite(self):
        headers = self._login()

        def upload(name: str):
            return self.client.post(
                "/api/upload", headers=headers,
                files={"file": (name, b"data", "application/octet-stream")})

        self.assertEqual(upload("../../evil.txt").json()["name"], "evil.txt")
        self.assertEqual(upload("evil.txt").json()["name"], "evil_1.txt")
        self.assertEqual(sorted(p.name for p in Path(self._tmp.name).iterdir()),
                         ["evil.txt", "evil_1.txt"])

    def test_websocket_requires_a_token_and_tolerates_bad_frames(self):
        headers = self._login()
        token = headers["Authorization"].removeprefix("Bearer ")

        with self.assertRaises(Exception):
            with self.client.websocket_connect("/ws?token=wrong"):
                pass

        with self.client.websocket_connect(f"/ws?token={token}") as socket:
            socket.send_text("this is not json")
            socket.send_text("[1, 2, 3]")
            socket.send_json({"type": "command", "text": "status report"})
            socket.send_json({"type": "command", "text": "second"})

        queued = []
        while not self.server._command_queue.empty():
            queued.append(self.server._command_queue.get_nowait())
        self.assertEqual(queued, ["status report", "second"])


if __name__ == "__main__":
    unittest.main()
