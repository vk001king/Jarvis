import unittest

from core.secret_guard import find_secret, mask

# Built at runtime so the repository never contains a string that looks like a
# live credential to a secret scanner.
GITHUB_TOKEN = "ghp_" + "A1b2" * 9
GOOGLE_KEY = "AIza" + "Sy0aB_c" * 5
JWT = ".".join(["eyJ" + "hbGciOiJIUzI1NiJ9", "eyJ" + "zdWIiOiIxMjM0In0", "sig" + "natureValue12"])


class SecretGuardTests(unittest.TestCase):
    def test_recognises_machine_issued_credentials(self):
        self.assertEqual(len(GOOGLE_KEY), 39)
        cases = {
            GITHUB_TOKEN: "GitHub token",
            "github_pat_" + "a1B2_" * 10: "GitHub token",
            GOOGLE_KEY: "Google API key",
            "sk-" + "proj0123456789abcdefXYZ": "API key",
            "xoxb-" + "123456789012-abcdefABCDEF": "Slack token",
            "AKIA" + "ABCDEFGHIJKLMNOP": "AWS access key",
            JWT: "JSON Web Token",
            "-----BEGIN RSA PRIVATE KEY-----\nMIIE...": "private key",
        }
        for value, kind in cases.items():
            with self.subTest(kind=kind):
                self.assertEqual(find_secret(value), kind)
                self.assertEqual(find_secret(f"my token is {value} ok"), kind)

    def test_ordinary_facts_are_not_mistaken_for_credentials(self):
        for value in (
            "pizza",
            "older sister, lives in Izmir",
            "my wifi password is hunter2",
            "wants to build a sky-high treehouse this summer",
            "https://github.com/someone/project",
            "0123456789abcdef0123456789abcdef01234567",
            "created a GitHub token on 2026-11-09",
            "",
            None,
            12345,
        ):
            with self.subTest(value=value):
                self.assertIsNone(find_secret(value))

    def test_mask_hides_the_value_but_keeps_the_surrounding_text(self):
        masked = mask(f"token {GITHUB_TOKEN} for work")

        self.assertNotIn(GITHUB_TOKEN, masked)
        self.assertEqual(masked, "token ghp_…[hidden] for work")
        self.assertEqual(mask("nothing to hide"), "nothing to hide")
        self.assertEqual(mask(None), "")


if __name__ == "__main__":
    unittest.main()
