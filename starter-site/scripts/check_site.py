#!/usr/bin/env python3
"""Block publication of an unfinished starter site. Standard library only."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SAMPLE_TEXT = (
    "your company",
    "a short, factual description",
    "say what you make",
    "describe the problem your customers face",
    "explain a real outcome people can expect",
    "show how your approach removes",
    "give visitors one more specific reason",
    "invite visitors to the one action",
    "a clear first step toward something better",
    "example.com",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.description = ""
        self.canonical = ""
        self.social_url = ""
        self.lang = ""
        self.h1_count = 0
        self.main_count = 0
        self.template_fields: list[str] = []
        self.local_paths: list[str] = []
        self.ids: set[str] = set()
        self.fragment_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"])
        if "data-template" in data:
            self.template_fields.append(data["data-template"] or tag)
        if tag == "html":
            self.lang = data.get("lang") or ""
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "meta":
            if data.get("name") == "description":
                self.description = data.get("content") or ""
            elif data.get("property") == "og:url":
                self.social_url = data.get("content") or ""
        elif tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href") or ""

        for key in ("href", "src"):
            value = data.get(key) or ""
            if value.startswith("#") and len(value) > 1:
                self.fragment_links.append(value[1:])
            if value.startswith("./") and value != "./":
                self.local_paths.append(value.split("?", 1)[0].split("#", 1)[0][2:])

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def main() -> int:
    problems: list[str] = []
    for name in ("index.html", "styles.css", "favicon.svg", "sitemap.xml"):
        if not (SITE / name).is_file():
            problems.append(f"Missing site/{name}")
    if problems:
        print("Site is not ready:\n- " + "\n- ".join(problems))
        return 1

    html = (SITE / "index.html").read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    if parser.template_fields:
        problems.append("Replace template fields: " + ", ".join(parser.template_fields))
    for sample in SAMPLE_TEXT:
        if sample in html.lower():
            problems.append(f"Replace sample content containing: {sample}")
    if not parser.lang:
        problems.append("Set the page language on <html>.")
    if not parser.title.strip() or not parser.description.strip():
        problems.append("Set a real page title and description.")
    if parser.h1_count != 1 or parser.main_count != 1:
        problems.append("Use one main element and one clear page headline.")
    for path in parser.local_paths:
        if not (SITE / path).is_file():
            problems.append(f"Broken local asset path: {path}")
    for fragment in parser.fragment_links:
        if fragment not in parser.ids:
            problems.append(f"Broken page section link: #{fragment}")

    parsed = urlsplit(parser.canonical)
    if parsed.scheme != "https" or not parsed.netloc:
        problems.append("Set the canonical URL to the real HTTPS page URL.")
    if parser.social_url != parser.canonical:
        problems.append("Make the social URL match the canonical URL.")

    try:
        tree = ET.parse(SITE / "sitemap.xml")
        locations = [node.text or "" for node in tree.findall(".//{*}loc")]
        if parser.canonical not in locations:
            problems.append("Include the canonical page URL in site/sitemap.xml.")
        if any("example.com" in loc.lower() for loc in locations):
            problems.append("Replace the sitemap example URL.")
    except ET.ParseError as exc:
        problems.append(f"Sitemap XML is invalid: {exc}")

    if problems:
        print("Site is not ready:\n- " + "\n- ".join(problems))
        return 1
    print(f"Site ready: {parser.title.strip()} — {parser.canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
