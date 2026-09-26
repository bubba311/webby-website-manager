# Measurement and model checks

## Distinguish the evidence

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Public fetch and HTML audit | What Webby received and parsed at a URL and time | Every crawler's access, rendered behavior, or indexing |
| Provider inspection and verified crawl logs | That service's observed crawl/index state or request | Future selection or all other services |
| Search impressions and visible citations | Recorded exposure within the named report's scope | Clicks, conversions, authority, or why exposure changed |
| Referral visits and successful visitor actions | Observed visits and outcomes under the stated attribution | All assistant use, including answers without a click |
| Chosen model reads supplied page content | Comprehension of the supplied material in that test | Organic discovery, retrieval ranking, or live search citations |
| Browser completes a specified task | That task worked in that environment | Every agent, device, task, or accessibility requirement |

Use owner-provided exports or an approved connection; never ask for secrets in chat. Keep account setup optional when it is not needed for the requested site change.

## Baseline and follow-up

- Record changed URLs, deployment time, material content changes, and a small stable set of realistic visitor questions and tasks. Include important unbranded questions as well as the company name. Match the audience's language and location. Avoid checking only prompts that already name the business.
- Where supplied, compare Google indexing/URL inspection and Search Console performance, including its generative AI report. Check effective inclusion controls if visibility is missing. Use Bing Webmaster Tools AI Performance for its supported surfaces. Reports have different units, aggregation, coverage, delays, and missing-data rules; preserve their labels rather than combine everything into one score. Citation counts are not clicks; Google generative-AI impressions are not a full cross-provider citation log.
- Compare the same pages, periods, countries/devices, and query cohorts where available. Leave enough time for recrawl and reporting, and note campaign, seasonal, demand, and platform changes. A before/after increase alone does not prove a specific edit caused it. Missing or suppressed data is not necessarily zero.
- For observed AI answers, record the exact question, provider/product, model if exposed, date, locale, search enabled/disabled, cited URL, quotation or factual representation, and inaccuracies. Repeated samples reveal variation; do not present a single answer as a stable ranking. Do not claim site-wide visibility from a handful of prompts.
- Measure what helps the startup: correct understanding, qualified visits, and completion of its chosen task. Visibility without accurate representation or useful action is incomplete. Feed observed misunderstandings back into specific content fixes.

## Model choice and comprehension

Users may choose a writing model for the whole site or individual sections. Honor the selection through the available model workflow and record which provider/model actually ran. Do not silently substitute another model. If access is unavailable, state the blocked assignment and the supported connection path.

Treat a target **reader** model separately from the **writer**. Having a model write text does not establish that the same model will retrieve, favor, cite, or recommend it in a deployed search product. Do not create crawler-specific sales claims, hidden instructions, or near-duplicate public pages to exploit a supposed authorship preference.

For a reader check, keep an approved fact sheet with exact expected answers, constraints, and unknowns. Provide the same visible page material and questions to each requested, connected model. Ask it to extract the offer, audience, price/requirements when stated, limitations, supporting evidence, and next action, identifying supporting passages and saying when information is absent. Evaluate factual errors, omissions, unsupported claims, and ambiguous actions against the fact sheet. Prefer a reviewer other than the writing model; if comparing drafts, conceal authorship and vary order to reduce judging bias.

Fix the demonstrated ambiguity and recheck. Label supplied-content tests as comprehension tests. Test live search or browser behavior separately with those capabilities enabled. Do not spend on endless model variations or label untested model-specific prose as an improvement; use the smallest comparison that answers the owner's question.
