---
name: webby-audit
description: Audit an approved website for search discovery, accurate AI answers, browser-agent tasks, and visual usability; verify evidence and fix the most consequential gaps.
---

# Webby website audit

Use this skill when the owner or a trusted teammate asks whether an approved website can be found, cited, read, or used by people, search systems, and browser agents. Also use it before handing off a new site or substantial content change. Follow `webby-github` for repository approval, branches, pull requests, and publication.

Treat these as separate outcomes: **accessible → discoverable → indexed → selected for an answer → accurately represented → useful action completed**. Evidence for one does not establish the next. The goal is a useful, distinctive website with measurable improvements, not a promise of third-party placement.

## Run the audit

1. Identify the owner-approved repository, live public URL, audience, and primary visitor task from existing context. Check `/var/lib/plow/webby-approved-repos` before reading or changing repository code. If the live URL is uncertain, confirm it with the owner; do not infer that a preview or localhost URL is production. Ask only for missing facts that change the work, such as the product's actual price or service area.
2. Run `webby-site-audit 'https://example.com/'` for the live page. It prints a human-readable report. Use `webby-site-audit 'https://example.com/' --format json` if structured output helps compare pages or prepare a pull request. On an existing cloud agent that has this skill installed in its persistent workspace but does not yet have the new image, run `python3 /var/lib/plow/workspace/skills/webby-audit/webby-site-audit 'https://example.com/'` instead. The command checks one URL at a time; run it separately for important pages such as home, product, pricing, and contact when those pages exist. Audit public HTTPS URLs. The `--allow-private` option is for local test fixtures, not site requests.
3. Read the result as observations from one fetched HTML response and its crawl files. The command does not execute JavaScript, prove indexing, validate schema meaning, or complete browser tasks. If fetching fails, report the URL, failure, and what remains unverified. A failed Webby fetch does not prove every crawler is blocked. Verify surprising findings against the actual response before recommending a change.
4. Read [site checks](references/site-checks.md) for crawl/render/index failures, content clarity, evidence, and page-specific rules. Inspect representative pages, not only the homepage. Use the checks relevant to the business; do not impose arbitrary heading counts, word counts, FAQs, links, or schema types.
5. If a browser is available, use [browser tasks](references/browser-tasks.md) to inspect phone and desktop renderings and complete one harmless visitor task. For visual fixes, also inspect an intermediate width and 200% zoom. If unavailable, mark rendered layout, accessibility-tree behavior, and task completion **verification needed**. Preserve visual hierarchy, type scale, spacing rhythm, line length, contrast, image treatment, mobile composition, and the site's identity as one system.
6. Use [measurement and model checks](references/measurement.md) when evaluating actual search outcomes, AI answer accuracy, or a chosen reader model. A writing model's preference for its own output is not evidence of real-world discovery or citations. Do not claim a test ran unless the intended model or service actually ran it.

## Prioritize the work

1. Fix blocked public pages, missing primary content, incorrect facts, broken primary actions, or inaccessible controls first.
2. Then resolve ambiguous product/audience language, inconsistent business details, misleading metadata, duplicate destinations, and missing proof for consequential claims.
3. Improve useful depth and visual clarity where they help a real visitor decision. Prefer an original demonstration, grounded comparison, or precise answer over adding generic pages.
4. Measure the changed pages and tasks. Treat optional integrations and experimental protocols as additions for a specific use case, not prerequisites for every startup.

Never invent business facts, credentials, reviews, measurements, dates, or sources. Do not add hidden persuasion aimed at assistants, crawler-only sales claims, mass near-duplicate pages, fake mentions, or extra machine-readable files solely to claim better visibility. Search access, user-initiated browsing, and model training are separate policy choices. Explain any proposed bot-access or indexing policy change and obtain the owner's decision before editing unless that exact change is already authorized.

## Report and follow through

Lead with the most consequential two or three actionable findings. For each, give the exact URL or file, observed evidence, likely impact, concrete fix, and how the fix will be verified. Separate **observed issue**, **verified OK**, **verification needed**, and **not applicable**; avoid a single overall score or fake precision. Record the date, pages and tasks sampled, browser/model used when applicable, and the limits of the audit. Distinguish an intended improvement from a measured result. Summarize unavailable owner reports or untested third-party behavior once, rather than interrupting every recommendation with a disclaimer.

If asked to fix findings, use `webby-github`: make a scoped branch, preserve the site's design, run the existing checks and another live or preview audit when available, then open a pull request with before/after evidence. Follow the owner's existing publication authorization; otherwise the owner reviews the specific pull request before Webby merges or publishes it. Recheck the live public URL after an authorized deployment, since previews cannot verify production headers, crawler policy, redirects, or index status.
