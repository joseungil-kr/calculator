import contextlib
from email.message import Message
from http.client import IncompleteRead
import importlib.util
import io
import json
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
        self.assertEqual(result["lastFailure"]["step"], "home")
        self.assertEqual(result["lastFailure"]["url"], "https://preview.example.com/")
        self.assertRegex(result["lastFailure"]["atUtc"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(result["lastFailure"]["errorCode"], "withheld")

    def test_home_and_robots_http_failures_report_the_fixed_stage_and_safe_url(self):
        headers = Message()
        headers["CF-RAY"] = "1234abcd1234abcd-DFW"

        def home_failure(_request, timeout):
            raise HTTPError("https://ignored.example/?token=secret", 403, "Forbidden", headers, io.BytesIO(b"private token=secret"))

        def robots_failure(request, timeout):
            if str(getattr(request, "full_url", request)).endswith("robots.txt"):
                raise HTTPError("https://ignored.example/robots.txt?token=secret", 403, "Forbidden", headers, io.BytesIO(b"error code: 1010"))
            return Response(
                f'<meta name="robots" content="noindex"><meta name="site-factory-revision" content="{REVISION}">',
                {"X-Robots-Tag": "noindex"},
            )

        for opener, step, url, code in (
            (home_failure, "home", "https://preview.example.com/", "withheld"),
            (robots_failure, "robots", "https://preview.example.com/robots.txt", "1010"),
        ):
            with self.subTest(step=step), contextlib.redirect_stdout(io.StringIO()):
                result = preview.verify("https://preview.example.com", REVISION, attempts=1, opener=opener)
            detail = result["lastFailure"]
            self.assertEqual(detail["step"], step)
            self.assertEqual(detail["url"], url)
            self.assertEqual(detail["errorCode"], code)
            self.assertNotIn("token=", str(detail))
            self.assertNotIn("fragment", str(detail))

    def test_error_body_is_withheld_unless_it_is_a_short_exact_ascii_error_code(self):
        headers = Message()
        for body, expected in (
            (b"error code: 123", "123"),
            (b"error code: 1010\n", "1010"),
            (b"error code: 1010\r\n", "1010"),
            (b"error code: 123\r", "withheld"),
            (b"error code: 123\nextra", "withheld"),
            (b"error code: 123" + b"0" * 52, "withheld"),
            (b"Authorization: Bearer private-token", "withheld"),
        ):
            with self.subTest(body=body):
                detail = preview.describe_failure(HTTPError("https://ignored.example/?token=secret", 403, "Forbidden", headers, io.BytesIO(body)))
                self.assertEqual(detail["errorCode"], expected)
                self.assertNotIn("private-token", str(detail))

    def test_failed_body_read_and_untrusted_diagnostic_attributes_are_withheld(self):
        class UnreadableBody:
            def read(self, _size):
                raise OSError("do not expose")

        error = HTTPError("https://ignored.example/", 403, "Forbidden", Message(), UnreadableBody())
        error.site_factory_step = "untrusted-step"
        error.site_factory_origin = "https://user:password@preview.example.com/private-secret?token=secret#fragment"
        error.site_factory_url = "https://attacker.example/secret"
        detail = preview.describe_failure(error)
        self.assertEqual(detail["step"], "unknown")
        self.assertIsNone(detail["url"])
        self.assertEqual(detail["errorCode"], "withheld")
        self.assertNotIn("secret", str(detail))

    def test_body_read_failures_preserve_http_result_and_retries(self):
        class UnreadableBody(io.BytesIO):
            def __init__(self, error):
                super().__init__()
                self.error = error

            def read(self, _size=-1):
                raise self.error

        for error in (OSError("read failed"), TimeoutError("timed out"), IncompleteRead(b"partial", 65)):
            with self.subTest(error=type(error).__name__):
                calls = []

                def opener(_request, timeout):
                    calls.append(timeout)
                    raise HTTPError("https://ignored.example/", 403, "Forbidden", Message(), UnreadableBody(error))

                with contextlib.redirect_stdout(io.StringIO()):
                    result = preview.verify("https://preview.example.com", REVISION, attempts=2, delay=0, opener=opener, sleeper=lambda _: None)
                self.assertEqual(calls, [15, 15])
                self.assertEqual(result["state"], "preview_verification_failed")
                self.assertEqual(result["lastFailure"]["status"], 403)
                self.assertEqual(result["lastFailure"]["errorCode"], "withheld")

    def test_safe_request_url_preserves_ipv6_brackets_and_rejects_bad_parse(self):
        self.assertEqual(preview.safe_request_url("https://[2001:db8::1]:8443", "home"), "https://[2001:db8::1]:8443/")
        self.assertIsNone(preview.safe_request_url("https://[broken", "home"))

    def test_unsafe_origin_never_appears_in_result_json_or_stdout(self):
        origin = "https://user:password@preview.example.com/private-secret?token=secret#fragment"
        def opener(_request, timeout):
            raise HTTPError("https://ignored.example/", 403, "Forbidden", Message(), io.BytesIO(b"error code: 1010\n"))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = preview.verify(origin, REVISION, attempts=1, opener=opener)
        serialized = json.dumps(result) + output.getvalue()
        self.assertIsNone(result["origin"])
        for secret in ("password", "private-secret", "token=secret", "fragment"):
            self.assertNotIn(secret, serialized)

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
