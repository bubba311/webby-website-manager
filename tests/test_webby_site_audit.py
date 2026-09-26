"""End-to-end checks for Webby's bounded, evidence-based site audit."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import runpy
import subprocess
import sys
import threading
import unittest


CLI = Path(__file__).resolve().parents[1] / "scripts" / "webby-site-audit"
ROBOTS_DECISION = runpy.run_path(str(CLI), run_name="webby_audit_test")["robots_decision"]


class FixtureHandler(BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, dict[str, str] | list[tuple[str, str]], bytes]] = {}
    seen: list[str] = []

    def do_GET(self) -> None:
        self.seen.append(self.path)
        status, headers, body = self.routes.get(self.path, (404, {"Content-Type": "text/plain"}, b"not found"))
        self.send_response(status)
        for key, value in (headers.items() if isinstance(headers, dict) else headers):
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        pass


class AuditCLITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def setUp(self) -> None:
        FixtureHandler.routes = {}
        FixtureHandler.seen = []

    def run_audit(self, path: str, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, str(CLI), self.origin + path, "--format", "json", *args],
            capture_output=True, text=True, timeout=15,
        )
        return result, json.loads(result.stdout)

    @staticmethod
    def by_id(report: dict, check_id: str) -> dict:
        return next(item for item in report["findings"] if item["id"] == check_id)

    def test_project_sitemap_and_missing_root_robots_are_not_errors(self) -> None:
        page_url = self.origin + "/project/"
        page = f"""<!doctype html><html lang="en"><head>
          <title>Example service and contact page</title>
          <meta name="description" content="A useful description of this example service.">
          <link rel="canonical" href="{page_url}">
          <script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebPage"}}</script>
          </head><body><main><h1>Example service</h1>
          <p>This page explains what the service does, who it is for, how to contact the team, and where to get more information.</p>
          <a href="/project/contact">Contact the team</a>
          <label for="email">Email</label><input id="email" type="email">
          <button type="button">Send request</button>
          </main></body></html>""".encode()
        FixtureHandler.routes = {
            "/project/": (200, {"Content-Type": "text/html; charset=utf-8"}, page),
            "/project/sitemap.xml": (200, {"Content-Type": "application/xml"},
                                     f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{page_url}</loc></url></urlset>'.encode()),
        }
        result, report = self.run_audit("/project/", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["robots_url"], self.origin + "/robots.txt")
        self.assertEqual(report["sitemap_url"], self.origin + "/project/sitemap.xml")
        self.assertEqual(self.by_id(report, "robots-root")["status"], "ok")
        self.assertEqual(self.by_id(report, "sitemap")["status"], "ok")
        self.assertEqual(self.by_id(report, "control-names")["status"], "ok")
        self.assertEqual(self.by_id(report, "crawlable-links")["status"], "ok")
        self.assertEqual(self.by_id(report, "jsonld-syntax")["status"], "ok")
        self.assertNotIn("/project/robots.txt", FixtureHandler.seen)

    def test_reports_observed_blockers_and_missing_accessible_names(self) -> None:
        page = b"""<!doctype html><html><head><title>Blocked page</title>
          <meta name="robots" content="noindex"><meta name="oai-searchbot" content="nosnippet">
          <script type="application/ld+json">{bad json}</script>
          </head><body><main><h1>Blocked page</h1>
          <a href="/next"><span></span></a><a href="javascript:void(0)">Fake action</a><input id="unlabelled">
          <p>Enough ordinary page text to make the audit's text check independent of the blockers being tested here.</p>
          </main></body></html>"""
        FixtureHandler.routes = {
            "/blocked": (200, {"Content-Type": "text/html", "X-Robots-Tag": "nosnippet"}, page),
            "/robots.txt": (200, {"Content-Type": "text/plain"},
                            b"User-agent: Googlebot\nAllow: /\n\nUser-agent: Bingbot\nDisallow: /blocked\n\nUser-agent: OAI-SearchBot\nDisallow: /blocked\n\nUser-agent: Claude-SearchBot\nDisallow: /blocked\n\nUser-agent: PerplexityBot\nDisallow: /blocked\n"),
        }
        result, report = self.run_audit("/blocked", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.by_id(report, "googlebot-access")["status"], "ok")
        self.assertEqual(self.by_id(report, "bingbot-access")["status"], "issue")
        self.assertEqual(self.by_id(report, "openai-search-access")["status"], "issue")
        self.assertEqual(self.by_id(report, "claude-search-access")["status"], "issue")
        self.assertEqual(self.by_id(report, "perplexity-search-access")["status"], "issue")
        self.assertEqual(self.by_id(report, "index-directives")["status"], "issue")
        self.assertIn("noindex", self.by_id(report, "index-directives")["evidence"])
        self.assertEqual(self.by_id(report, "control-names")["status"], "issue")
        self.assertEqual(self.by_id(report, "crawlable-links")["status"], "issue")
        self.assertIn("<input>#unlabelled", self.by_id(report, "control-names")["evidence"])
        self.assertEqual(self.by_id(report, "jsonld-syntax")["status"], "issue")

    def test_oai_specific_meta_does_not_create_google_indexing_finding(self) -> None:
        FixtureHandler.routes = {
            "/target": (200, {"Content-Type": "text/html"},
                        b'<html><head><title>Target</title><meta name="oai-searchbot" content="noindex"></head>'
                        b'<body><main><h1>Target</h1><p>A readable public page with a direct link to more information.</p>'
                        b'<a href="/more">Learn more</a></main></body></html>'),
        }
        result, report = self.run_audit("/target", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.by_id(report, "index-directives")["status"], "ok")

    def test_empty_sitemap_requires_verification(self) -> None:
        FixtureHandler.routes = {
            "/project/": (200, {"Content-Type": "text/html"},
                          b'<html><head><title>Project</title></head><body><main><h1>Project</h1></main></body></html>'),
            "/project/sitemap.xml": (200, {"Content-Type": "application/xml"}, b"<urlset></urlset>"),
        }
        result, report = self.run_audit("/project/", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.by_id(report, "sitemap-empty")["status"], "verify")

    def test_invalid_sitemap_does_not_hide_valid_fallback(self) -> None:
        FixtureHandler.routes = {
            "/project/": (200, {"Content-Type": "text/html"}, b"<html><head><title>Project</title></head><body><main><h1>Project</h1></main></body></html>"),
            "/project/sitemap.xml": (200, {"Content-Type": "application/xml"}, b"<bad>"),
            "/sitemap.xml": (200, {"Content-Type": "application/xml"},
                             f"<urlset><url><loc>{self.origin}/project/</loc></url></urlset>".encode()),
        }
        result, report = self.run_audit("/project/", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.by_id(report, "sitemap-invalid")["status"], "issue")
        self.assertEqual(report["sitemap_url"], self.origin + "/sitemap.xml")

    def test_crawler_specific_header_is_not_global_index_block(self) -> None:
        FixtureHandler.routes = {
            "/target": (200, {"Content-Type": "text/html", "X-Robots-Tag": "otherbot: noindex"},
                        b"<html><head><title>Target</title></head><body><main><h1>Target</h1></main></body></html>"),
        }
        result, report = self.run_audit("/target", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.by_id(report, "index-directives")["status"], "verify")

    def test_duplicate_headers_and_none_max_snippet_are_index_blockers(self) -> None:
        page = b'<html><head><title>Target</title><meta name="robots" content="none, max-snippet:0"></head><body><main><h1>Target</h1></main></body></html>'
        FixtureHandler.routes = {
            "/target": (200, [("Content-Type", "text/html"), ("X-Robots-Tag", "noindex"),
                               ("X-Robots-Tag", "nofollow")], page),
        }
        result, report = self.run_audit("/target", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = self.by_id(report, "index-directives")["evidence"]
        self.assertEqual(self.by_id(report, "index-directives")["status"], "issue")
        self.assertIn("noindex", evidence)
        self.assertIn("none", evidence)
        self.assertIn("max-snippet:0", evidence)

    def test_aria_labelledby_is_uncertain_and_named_anchor_without_href_is_bad_link(self) -> None:
        FixtureHandler.routes = {
            "/target": (200, {"Content-Type": "text/html"},
                        b'<html><head><title>Target</title></head><body><main><h1>Target</h1>'
                        b'<span id="action-name">Submit</span><button aria-labelledby="action-name"></button>'
                        b'<a>Learn more</a></main></body></html>'),
        }
        result, report = self.run_audit("/target", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.by_id(report, "control-names")["status"], "verify")
        self.assertEqual(self.by_id(report, "crawlable-links")["status"], "issue")

    def test_html_challenge_at_robots_is_not_reported_as_crawler_permission(self) -> None:
        FixtureHandler.routes = {
            "/target": (200, {"Content-Type": "text/html"},
                        b"<html><head><title>Target</title></head><body><main><h1>Target</h1></main></body></html>"),
            "/robots.txt": (200, {"Content-Type": "text/html"}, b"<html><body>Challenge</body></html>"),
        }
        result, report = self.run_audit("/target", "--allow-private")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.by_id(report, "robots-root")["status"], "verify")
        self.assertFalse(any(item["id"] == "googlebot-access" for item in report["findings"]))

    def test_private_url_requires_explicit_local_test_flag(self) -> None:
        result, report = self.run_audit("/",)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.by_id(report, "page-fetch")["status"], "issue")
        self.assertEqual(FixtureHandler.seen, [])

    def test_redirect_to_non_http_target_is_rejected(self) -> None:
        FixtureHandler.routes = {
            "/redirect": (302, {"Location": "file:///etc/passwd"}, b""),
        }
        result, report = self.run_audit("/redirect", "--allow-private")
        self.assertEqual(result.returncode, 2)
        self.assertIn("HTTPS URL", self.by_id(report, "page-fetch")["evidence"])
        self.assertEqual(FixtureHandler.seen, ["/redirect"])

    def test_page_response_size_is_bounded(self) -> None:
        FixtureHandler.routes = {
            "/large": (200, {"Content-Type": "text/html"}, b"x" * (512 * 1024 + 1)),
        }
        result, report = self.run_audit("/large", "--allow-private")
        self.assertEqual(result.returncode, 2)
        self.assertIn("exceeds", self.by_id(report, "page-fetch")["evidence"])


class RobotsPolicyTest(unittest.TestCase):
    def test_longest_matching_rule_and_allow_tie_break(self) -> None:
        rules = "User-agent: *\nDisallow: /\nAllow: /public/\nDisallow: /public/private/*\nAllow: /public/private/allowed$\n"
        self.assertEqual(ROBOTS_DECISION(rules, "Googlebot", "https://example.com/public/page")[0], True)
        self.assertEqual(ROBOTS_DECISION(rules, "Googlebot", "https://example.com/public/private/other")[0], False)
        self.assertEqual(ROBOTS_DECISION(rules, "Googlebot", "https://example.com/public/private/allowed")[0], True)
        tied = "User-agent: *\nDisallow: /same\nAllow: /same\n"
        self.assertEqual(ROBOTS_DECISION(tied, "Bingbot", "https://example.com/same")[0], True)

    def test_dollar_anchor_and_specific_group(self) -> None:
        rules = "User-agent: *\nDisallow: /draft$\n\nUser-agent: OAI-SearchBot\nAllow: /\n"
        self.assertEqual(ROBOTS_DECISION(rules, "Googlebot", "https://example.com/draft")[0], False)
        self.assertEqual(ROBOTS_DECISION(rules, "Googlebot", "https://example.com/drafts")[0], True)
        self.assertEqual(ROBOTS_DECISION(rules, "OAI-SearchBot", "https://example.com/draft")[0], True)

    def test_encoded_or_non_ascii_rules_require_verification(self) -> None:
        self.assertIsNone(ROBOTS_DECISION("User-agent: *\nDisallow: /caf%C3%A9\n", "Googlebot", "https://example.com/caf%C3%A9")[0])
        self.assertIsNone(ROBOTS_DECISION("User-agent: *\nDisallow: /bar/%62\n", "Googlebot", "https://example.com/bar/baz")[0])
        self.assertIsNone(ROBOTS_DECISION("User-agent: *\nDisallow: /caf\u00e9\n", "Googlebot", "https://example.com/caf\u00e9")[0])

    def test_many_wildcards_are_bounded(self) -> None:
        complex_rule = "User-agent: *\nDisallow: /" + "*a" * 33 + "$\n"
        self.assertIsNone(ROBOTS_DECISION(complex_rule, "Googlebot", "https://example.com/" + "a" * 100)[0])


if __name__ == "__main__":
    unittest.main()
