#!/usr/bin/env python3
"""Block publication of an unfinished or hard-to-use starter site."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
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
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


@dataclass
class Action:
    tag: str
    destination: str | None
    label: str
    labelledby: str
    words: list[str] = field(default_factory=list)

    def has_name(self, page_ids: set[str]) -> bool:
        if any(character.isalnum() for character in self.label + " ".join(self.words)):
            return True
        references = self.labelledby.split()
        return bool(references) and all(reference in page_ids for reference in references)


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
        self.references: list[tuple[str, str, str]] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.actions: list[Action] = []
        self._open_actions: list[Action] = []
        self._elements: list[tuple[str, bool]] = []
        self.unlabelled_images = 0
        self.blocks_indexing = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            if data["id"] in self.ids:
                self.duplicate_ids.add(data["id"])
            self.ids.add(data["id"])
        if "data-template" in data:
            self.template_fields.append(data["data-template"] or tag)
        hidden = (self._elements[-1][1] if self._elements else False) or (data.get("aria-hidden") or "").lower() == "true" or "hidden" in data
        if tag not in VOID_ELEMENTS:
            self._elements.append((tag, hidden))
        if tag == "html":
            self.lang = data.get("lang") or ""
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "meta":
            name = (data.get("name") or "").lower()
            if name == "description":
                self.description = data.get("content") or ""
            elif data.get("property") == "og:url":
                self.social_url = data.get("content") or ""
            if (name == "robots" or name.endswith("bot")) and any(
                directive in {"noindex", "none"}
                for directive in (data.get("content") or "").lower().replace(",", " ").split()
            ):
                self.blocks_indexing = True
        elif tag == "link" and data.get("rel") == "canonical":
            self.canonical = data.get("href") or ""
        elif tag == "img":
            if "alt" not in data:
                self.unlabelled_images += 1
            elif data["alt"] and self._open_actions and not hidden:
                self._open_actions[-1].words.append(data["alt"])

        if tag in {"a", "button"}:
            self._open_actions.append(Action(
                tag=tag,
                destination=data.get("href") if tag == "a" else None,
                label=data.get("aria-label") or "",
                labelledby=data.get("aria-labelledby") or "",
            ))

        for key in ("href", "src"):
            if key in data:
                self.references.append((tag, key, data.get(key) or ""))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag in {"a", "button"} and self._open_actions:
            action = self._open_actions.pop()
            if action.tag == tag:
                self.actions.append(action)
        for index in range(len(self._elements) - 1, -1, -1):
            if self._elements[index][0] == tag:
                del self._elements[index:]
                break

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self._open_actions and not (self._elements[-1][1] if self._elements else False):
            self._open_actions[-1].words.append(data)


def check_reference(tag: str, key: str, value: str, site: Path, page_ids: set[str]) -> str | None:
    value = value.strip()
    if not value:
        return f"Empty {key} on <{tag}>."
    try:
        url = urlsplit(value)
    except ValueError:
        return f"Unusable {key} on <{tag}>: {value}"
    if url.scheme:
        if url.scheme in {"http", "https"} and url.netloc:
            return None
        if tag == "a" and url.scheme in {"mailto", "tel"} and url.path:
            return None
        if key == "src" and url.scheme == "data":
            return None
        return f"Unusable {key} on <{tag}>: {value}"
    if url.netloc:
        return None
    if url.path.startswith("/"):
        return f"Root-relative {key} may break a project site: {value}"
    if not url.path and url.fragment and url.fragment not in page_ids:
        return f"Broken page section link: #{url.fragment}"
    if not url.path:
        return None
    path = (site / unquote(url.path)).resolve()
    if not path.is_relative_to(site.resolve()):
        return f"Local {key} points outside this site: {value}"
    if path.is_dir():
        path /= "index.html"
    if not path.is_file():
        return f"Broken local {key}: {value}"
    if tag == "a" and path == site / "index.html" and url.fragment and url.fragment not in page_ids:
        return f"Broken page section link: #{url.fragment}"
    return None


def check_site(root: Path) -> tuple[list[str], PageParser | None]:
    problems: list[str] = []
    site = root / "site"
    for name in ("index.html", "styles.css", "favicon.svg", "sitemap.xml"):
        if not (site / name).is_file():
            problems.append(f"Missing site/{name}")
    if problems:
        return problems, None

    html = (site / "index.html").read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    parser.close()
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
    if parser.duplicate_ids:
        problems.append("Use each page section ID once: " + ", ".join(sorted(parser.duplicate_ids)))
    if parser.blocks_indexing:
        problems.append("The page asks search crawlers not to list it; review the robots meta tag before publishing.")
    if parser.unlabelled_images:
        problems.append("Give each image an alt attribute; use alt=\"\" for decoration.")
    for action in parser.actions:
        if not action.has_name(parser.ids):
            problems.append(f"Give every <{action.tag}> a readable name or aria-label.")
    for tag, key, value in parser.references:
        issue = check_reference(tag, key, value, site, parser.ids)
        if issue:
            problems.append(issue)

    parsed = urlsplit(parser.canonical)
    if parsed.scheme != "https" or not parsed.netloc:
        problems.append("Set the canonical URL to the real HTTPS page URL.")
    if parser.social_url != parser.canonical:
        problems.append("Make the social URL match the canonical URL.")

    try:
        tree = ET.parse(site / "sitemap.xml")
        locations = [node.text or "" for node in tree.findall(".//{*}loc")]
        if parser.canonical not in locations:
            problems.append("Include the canonical page URL in site/sitemap.xml.")
        if any("example.com" in loc.lower() for loc in locations):
            problems.append("Replace the sitemap example URL.")
    except ET.ParseError as exc:
        problems.append(f"Sitemap XML is invalid: {exc}")

    return problems, parser


def main() -> int:
    problems, parser = check_site(ROOT)
    if problems:
        print("Site is not ready:\n- " + "\n- ".join(problems))
        return 1
    assert parser is not None
    print(f"Site ready: {parser.title.strip()} — {parser.canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
