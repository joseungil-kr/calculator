import contextlib
from email.message import Message
import importlib.util
import io
from pathlib import Path
import unittest
from urllib.error import HTTPError


path = Path(__file__).resolve().parents[1] / "verify_preview.py"
spec = importlib.util.spec_from_file_location("verify_preview", path)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)
REVISION = "a" * 40


class Response:
    def __init__(self, body, headers=None):
        self.body = body.encode()
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self):
        return self.body


class PreviewVerificationTests(unittest.TestCase):
    def test_exact_public_noindex_passes_without_failure_metadata(self):
        def opener(request, timeout):
            if str(getattr(request, "full_url", request)).endswith("robots.txt"):
                return Response("User-agent: *\nDisallow: /")
            return Response(f'<meta name="robots" content="noindex"><meta name="site-factory-revision" content="{REVISION}">', {"X-Robots-Tag": "noindex, nofollow"})
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = preview.verify("https://preview.example.com", REVISION, attempts=1, opener=opener)
        self.assertEqual(result["state"], "preview_verified")
        self.assertEqual(output.getvalue(), "")

    def test_http_failure_remains_failure_with_allowlisted_diagnostics(self):
        headers = Message()
        for name, value in {
            "Server": "cloudflare",
            "CF-RAY": "1234abcd1234abcd-DFW",
            "Via": "token=DoNotRevealCredential",
            "Set-Cookie": "session=alsoDoNotReveal",
            "Authorization": "Bearer NeverPrintThis",
            "Content-Type": "text/html",
        }.items():
            headers[name] = value
        def opener(_request, timeout):
            raise HTTPError(
                "https://preview.example.com/", 403, "Forbidden", headers,
                io.BytesIO(b'<html>{"token": "ShortSecret42"} Authorization: Bearer ShortSecret42 password=my long password 2001:db8::1</html>'),
            )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = preview.verify("https://preview.example.com", REVISION, attempts=2, delay=0, opener=opener, sleeper=lambda _: None)
        self.assertEqual(result["state"], "preview_verification_failed")
        self.assertEqual(result["lastFailure"]["status"], 403)
        logged = output.getvalue() + str(result)
        for secret in ("DoNotRevealCredential", "alsoDoNotReveal", "NeverPrintThis", "ShortSecret42", "my long password", "2001:db8::1", "Set-Cookie", "Authorization"):
            self.assertNotIn(secret, logged)
        self.assertTrue(result["lastFailure"]["serverIsCloudflare"])
        self.assertEqual(result["lastFailure"]["cfRay"], "1234abcd1234abcd-DFW")
        self.assertEqual(result["lastFailure"]["contentType"], "text/html")
        self.assertTrue(result["lastFailure"]["viaPresent"])
        self.assertNotIn("publicBodyExcerpt", result["lastFailure"])

    def test_unshaped_cf_ray_and_arbitrary_header_values_are_never_logged(self):
        headers = Message()
        headers["Server"] = "cloudflare password=BadValue"
        headers["CF-RAY"] = "token=OtherBadValue"
        headers["Content-Type"] = "application/x-private-secret"
        error = HTTPError("https://preview.example.com/", 403, "Forbidden", headers, io.BytesIO(b"private body"))
        detail = preview.describe_failure(error)
        self.assertFalse(detail["serverIsCloudflare"])
        self.assertIsNone(detail["cfRay"])
        self.assertEqual(detail["contentType"], "other")
        self.assertNotIn("BadValue", str(detail))

    def test_missing_revision_never_reports_pass(self):
        def opener(_request, timeout):
            return Response(f'<meta name="robots" content="noindex"><meta name="site-factory-revision" content="wrong">Expected text {REVISION}', {"X-Robots-Tag": "noindex"})
        with contextlib.redirect_stdout(io.StringIO()):
            result = preview.verify("https://preview.example.com", REVISION, attempts=1, opener=opener)
        self.assertEqual(result["state"], "preview_verification_failed")
        self.assertEqual(result["lastFailure"]["kind"], "ValueError")

    def test_noindex_header_requires_exact_directive(self):
        def opener(_request, timeout):
            return Response(
                f'<meta name="robots" content="noindex"><meta name="site-factory-revision" content="{REVISION}">',
                {"X-Robots-Tag": "not-noindex"},
            )
        with contextlib.redirect_stdout(io.StringIO()):
            result = preview.verify("https://preview.example.com", REVISION, attempts=1, opener=opener)
        self.assertEqual(result["state"], "preview_verification_failed")

    def test_robots_requires_universal_whole_site_exclusion(self):
        def opener(request, timeout):
            if str(getattr(request, "full_url", request)).endswith("robots.txt"):
                return Response("User-agent: *\nDisallow: /private/\n# Disallow: /")
            return Response(
                f'<meta name="robots" content="noindex"><meta name="site-factory-revision" content="{REVISION}">',
                {"X-Robots-Tag": "noindex, nofollow"},
            )
        with contextlib.redirect_stdout(io.StringIO()):
            result = preview.verify("https://preview.example.com", REVISION, attempts=1, opener=opener)
        self.assertEqual(result["state"], "preview_verification_failed")
        self.assertTrue(preview.robots_blocks_all("# isolate preview\n User-agent : * \n Disallow: / # all routes"))
        for invalid in (
            "User-agent: *\nDisallow: /\nAllow: /",
            "User-agent: *\nDisallow: /\nAllow: /public/",
            "User-agent: *\nDisallow: /\nUser-agent: Googlebot\nDisallow: /private/",
            "User-agent: Googlebot\nDisallow: /",
        ):
            self.assertFalse(preview.robots_blocks_all(invalid))


if __name__ == "__main__":
    unittest.main()
