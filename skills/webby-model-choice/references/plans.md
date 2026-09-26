# Plans and receipts

Keep configuration, plans containing private facts, outputs, and credentials outside the website checkout. `webby-model-connect init` reports the private configuration path. Provider profile names are local names; the model field is an ID available through that provider, or an intentional provider alias.

## Provider configuration

```json
{
  "version": 1,
  "providers": {
    "codex": {"kind": "codex", "auth_dir": "/var/lib/plow/models/codex", "default_model": "OWNER_SELECTED_MODEL"},
    "claude": {"kind": "claude", "auth_dir": "/var/lib/plow/models/claude"},
    "openai": {"kind": "openai", "api_key_env": "WEBBY_OPENAI_API_KEY"},
    "anthropic": {"kind": "anthropic", "api_key_env": "WEBBY_ANTHROPIC_API_KEY"},
    "gemini": {"kind": "gemini", "api_key_env": "WEBBY_GEMINI_API_KEY"},
    "router": {"kind": "compatible", "base_url": "https://openrouter.ai/api/v1", "api_key_env": "WEBBY_OPENROUTER_API_KEY"}
  }
}
```

Replace example model names before running. An API profile uses exactly one of `api_key_env` or `api_key_file`. The latter must point to a private, owner-owned, nonsymlink file outside the site checkout; the setup helper writes it with mode 600. Never put the key itself in configuration. Subscription profiles can omit `auth_dir` to use the current local CLI login; an installation's own explicit directory keeps its logins separate. Custom compatible endpoints require owner configuration, HTTPS, and a public host. Compatible services differ: use `token_parameter: "max_completion_tokens"` if the service requires it instead of the default `max_tokens`. Unsupported parameters or response shapes produce a failure, not a claim of universal compatibility.

## Two writers, one file, then a reader

Webby prepares these boundaries in a working branch when the source does not already have suitable markers:

```html
<!-- webby:hero:start -->
<section id="hero">Current hero content</section>
<!-- webby:hero:end -->
<!-- webby:details:start -->
<section id="details">Current product details</section>
<!-- webby:details:end -->
```

Example plan (replace model placeholders and use the real paths, facts, and destinations):

```json
{
  "version": 1,
  "brief": "Acme helps independent shops manage inventory. Preserve the approved facts, action destination, and established visual system.",
  "context_files": ["site/styles.css"],
  "jobs": [
    {"id": "hero", "provider": "codex", "model": "SELECTED_CODEX_MODEL", "path": "site/index.html", "section": {"start": "<!-- webby:hero:start -->", "end": "<!-- webby:hero:end -->"}, "task": "Refine the hero composition and explain the offer clearly without inventing business facts.", "max_output_tokens": 2048, "timeout_seconds": 120},
    {"id": "details", "provider": "claude", "model": "SELECTED_CLAUDE_MODEL", "path": "site/index.html", "section": {"start": "<!-- webby:details:start -->", "end": "<!-- webby:details:end -->"}, "task": "Write concise product details from the supplied facts. Preserve the page voice and working action.", "max_output_tokens": 2048, "timeout_seconds": 120},
    {"id": "reader", "operation": "review", "provider": "claude", "model": "SELECTED_READER_MODEL", "path": "site/index.html", "review_proposed": true, "task": "Extract the offer, audience, and next action. Quote support and flag ambiguities or unsupported claims.", "max_output_tokens": 2048, "timeout_seconds": 120}
  ]
}
```

Omit `section` to draft a whole file. Enumerate files to cover a whole site. A review job never creates a source replacement. Set `allow_model_alias: true` only when the owner intentionally selected a provider alias or documented snapshot mapping; otherwise a reported different model causes rejection. Receipts distinguish the requested model from provider-reported evidence. Codex may not report its actual served model, so do not invent one.

## Accepting output

The output directory contains `receipt.json`, `changes.patch`, and proposed source files when the plan succeeds. Review jobs add structured findings to the receipt. Validate the exact artifact paths reported by the program; do not assume a patch exists after failure. A failed plan can retain completed-job receipts for diagnosis but must not be applied as a completed plan. Provider refusals, truncation, missing credentials, boundary violations, and unexpected model IDs are actionable failures.

The evidence quotes in a reader result must occur in the supplied text. This catches fabricated quotations; Webby must still assess whether the claim follows from the quote and whether the underlying business fact is true. For a stronger check, compare the target reader with an independent model and the owner-grounded fact sheet. Repeat live searches only within the selected service's supported access and agreed usage; record date, query, model/service, cited URL, and failures without turning a small sample into a ranking forecast.
