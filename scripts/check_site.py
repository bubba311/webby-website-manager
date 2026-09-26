#!/usr/bin/env python3
"""Check links and local assets in Webby's static landing page."""

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re


SITE = Path(__file__).resolve().parents[1] / "site"
PAGE = SITE / "index.html"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.h1_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "h1":
            self.h1_count += 1
        for key in ("href", "src"):
            if values.get(key):
                self.links.append((tag, values[key]))


def local_file(url: str) -> Path | None:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or url.startswith(("#", "//")):
        return None
    path = (SITE / unquote(parts.path)).resolve()
    if not path.is_relative_to(SITE.resolve()):
        raise ValueError(f"Link escapes site directory: {url}")
    return path


def main() -> None:
    parser = PageParser()
    parser.feed(PAGE.read_text(encoding="utf-8"))
    errors: list[str] = []
    if parser.h1_count != 1:
        errors.append(f"Expected one h1, found {parser.h1_count}")
    errors.extend(f"Duplicate id: {key}" for key, count in Counter(parser.ids).items() if count > 1)
    for tag, url in parser.links:
        if url.startswith("#") and url[1:] not in parser.ids:
            errors.append(f"{tag} has missing anchor: {url}")
        else:
            try:
                path = local_file(url)
                if path and not path.is_file():
                    errors.append(f"{tag} has missing asset: {url}")
            except ValueError as error:
                errors.append(str(error))
    for stylesheet in SITE.glob("*.css"):
        for raw in re.findall(r"url\(\s*['\"]?([^)'\"]+)", stylesheet.read_text(encoding="utf-8")):
            try:
                path = local_file(raw)
                if path and not path.is_file():
                    errors.append(f"{stylesheet.name} has missing asset: {raw}")
            except ValueError as error:
                errors.append(str(error))
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Verified {len(parser.links)} page links/assets, CSS assets, and unique anchors.")


if __name__ == "__main__":
    main()
