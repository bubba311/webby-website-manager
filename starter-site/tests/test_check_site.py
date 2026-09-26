"""The starter preflight should catch launch-breaking page defects."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


CHECK_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_site.py"
PAGE = """<!doctype html>
<html lang="en"><head>
  <title>Acme — Scheduling for small teams</title>
  <meta name="description" content="Acme helps small teams plan work and see the next step in one place.">
  <link rel="canonical" href="https://acme.test/">
  <meta property="og:url" content="https://acme.test/">
  <link rel="stylesheet" href="./styles.css">
  <link rel="icon" href="./favicon.svg">
</head><body>
  <a href="#main">Skip to content</a>
  <main id="main">
    <h1>Plan work together with Acme</h1>
    <p>Small teams use Acme to see owners, dates, and next steps.</p>
    <img src="./feature.svg" alt="A shared weekly plan">
    <a href="mailto:hello@acme.test">Email the team</a>
  </main>
</body></html>
"""


class CheckSiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "scripts").mkdir()
        (self.root / "site").mkdir()
        shutil.copy2(CHECK_SCRIPT, self.root / "scripts" / "check_site.py")
        self.page = self.root / "site" / "index.html"
        self.page.write_text(PAGE, encoding="utf-8")
        for name in ("styles.css", "favicon.svg", "feature.svg"):
            (self.root / "site" / name).write_text("", encoding="utf-8")
        (self.root / "site" / "sitemap.xml").write_text(
            '<urlset><url><loc>https://acme.test/</loc></url></urlset>', encoding="utf-8"
        )

    def run_check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "check_site.py")],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def change_page(self, old: str, new: str) -> None:
        html = self.page.read_text(encoding="utf-8")
        assert old in html
        self.page.write_text(html.replace(old, new), encoding="utf-8")

    def test_ready_page_passes(self) -> None:
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unlabelled_action_or_image_fails(self) -> None:
        self.change_page("Email the team</a>", "<span aria-hidden=\"true\">↗</span></a>")
        self.change_page('alt="A shared weekly plan"', "")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("readable name", result.stdout)
        self.assertIn("alt attribute", result.stdout)

    def test_bad_link_and_project_path_fail(self) -> None:
        self.change_page('href="mailto:hello@acme.test"', 'href="javascript:void(0)"')
        self.change_page('href="./styles.css"', 'href="/styles.css"')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unusable href", result.stdout)
        self.assertIn("Root-relative href", result.stdout)

    def test_missing_local_destination_fails(self) -> None:
        self.change_page('href="mailto:hello@acme.test"', 'href="./contact.html"')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Broken local href", result.stdout)

    def test_accidental_noindex_fails(self) -> None:
        self.change_page("</head>", '<meta name="robots" content="noindex, follow"></head>')
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("asks search crawlers not to list it", result.stdout)


if __name__ == "__main__":
    unittest.main()
