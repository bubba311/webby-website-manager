---
name: webby-audit
description: Audit an owner-approved website for access, search readiness, clear answers, and verifiable facts; report evidence and propose focused fixes.
---

# Webby website audit

Use this skill when the owner or a trusted teammate asks whether an approved website can be found, read, and used by people, search crawlers, and browser agents. This is a practical site-quality review, not a prediction of third-party placement. Follow `webby-github` for repository approval, branches, pull requests, and publication.

## Run the audit

1. Identify the owner-approved repository and its live public URL. Check `/var/lib/plow/webby-approved-repos` before reading or changing repository code. If the live URL is uncertain, confirm it with the owner; do not infer that a preview or localhost URL is production.
2. Run `webby-site-audit 'https://example.com/'` for the live page. It prints a human-readable report. Use `webby-site-audit 'https://example.com/' --format json` if structured output helps compare pages or prepare a pull request. On an existing cloud agent that has this skill installed in its persistent workspace but does not yet have the new image, run `python3 /var/lib/plow/workspace/skills/webby-audit/webby-site-audit 'https://example.com/'` instead. The command checks one URL at a time; run it separately for important pages such as home, product, pricing, and contact when those pages exist. Audit public HTTPS URLs. The `--allow-private` option is for local test fixtures, not site requests.
3. Read the result as observations from the fetched page and its crawl files. If fetching fails, report the URL, failure, and what remains unverified. Do not treat a failed fetch as proof that every crawler is blocked. When a finding seems surprising, open the relevant live URL or response and verify it before recommending a change.
4. Check the page's purpose before interpreting a finding. Do not enforce fixed counts of headings, questions, or external links. Recommend structured data only when its type matches truthful, visible page content. Do not invent company facts, credentials, testimonials, prices, dates, or sources to satisfy a check.
5. If a browser is available, inspect a narrow phone and desktop rendering, then try one harmless task through visible controls using the keyboard. Look for clipping, weak hierarchy, unreadable text, low-contrast actions, hidden focus, layout shifts, and controls that differ between the screenshot and their accessible names. For a proposed visual fix, also check an intermediate width and 200% zoom. If a browser is unavailable, mark rendered layout and task completion **verification needed**; the HTML audit cannot establish either result.

## What to look for

- **Access and discovery:** successful public response; readable HTML; robots and `noindex` controls; canonical URL; useful links and sitemap coverage. Check search crawler rules separately from model-training preferences. A sitemap or permissive robots rule helps discovery but does not establish actual crawler access through a firewall or guarantee indexing.
- **Meaning and answer clarity:** descriptive title and headings; a concise explanation of what the business offers, who it serves, and how to act; accurate metadata; useful original details and answers to real visitor questions; structured data only when its type and claims agree with visible content. Do not add repetitive questions or generic filler for search.
- **Trust and consistency:** real contact and business facts; dates on time-sensitive content; support for factual claims; agreement between the site and owner-provided business profiles or listings. Treat off-site listings, reviews, and search performance as **verification needed** unless a source was actually checked.
- **Experience and design:** inspect whether links have real destinations, buttons have names, forms have associated labels, and a browser agent can complete a harmless task using visible controls. Review type scale, spacing rhythm, line length, contrast, visual hierarchy, image treatment, and responsive composition together. Preserve the site's visual identity, accessibility, and mobile usability while fixing problems.

Do not add extra machine-readable files solely to claim better visibility. Do not change `robots.txt`, crawler-specific rules, `noindex`, or other bot-access policy automatically; explain the observed rule and ask the owner before proposing a policy change.

## Report and follow through

Lead with the most consequential two or three actionable findings. For each, give the exact page or file URL, observed evidence, likely user or crawler impact, and a concrete fix. Separate **observed issue**, **verified OK**, **verification needed**, and **not applicable**; avoid a single overall score or fake precision. State what the audit did not measure, especially actual indexing, third-party placement, off-site profile quality, and any untested rendered or browser-agent flow. If the owner provides search-performance reports or an approved connection, use them to compare real pages and queries after publication; otherwise offer that as a later measurement step without asking for credentials in chat.

If asked to fix findings, use `webby-github`: make a scoped branch, preserve the site's design, run the existing checks and another live or preview audit when available, then open a pull request with before/after evidence. The owner reviews the specific pull request before Webby merges or publishes it. For bot-access policy changes, get the owner's decision on the proposed rule before editing, even on a draft branch.
