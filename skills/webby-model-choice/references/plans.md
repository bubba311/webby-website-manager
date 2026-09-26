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

## Review actual screenshots

When an owner selects a visual reviewer, use a connected model that supports image input through that interface. Default reviews may use the host's already configured image-inference route without a new account connection; this plan is for the selected-model runner. Render the proposed site first, then place the captured visible text and screenshots in one artifact directory. Use that directory as `--repo`, with the plan and new output directory outside it:

```json
{
  "version": 1,
  "brief": "Review the captured page design.",
  "context_files": ["1440-accessibility.txt", "375-text.txt"],
  "jobs": [{
    "id": "visual-review",
    "operation": "review",
    "provider": "CONNECTED_PROFILE",
    "model": "SELECTED_VISION_MODEL",
    "path": "1440-text.txt",
    "images": ["1440-viewport.png", "375-viewport.png"],
    "task": "Inspect the actual screenshots for hierarchy, type, spacing, alignment, contrast, and clipping. Give concrete locations and useful improvements, without inventing defects. Keep text evidence as exact quotes from the primary visible text. State which interactions remain untested.",
    "max_output_tokens": 2048,
    "timeout_seconds": 120
  }]
}
```

```sh
webby-model-draft validate --config CONFIG --plan PLAN --repo CAPTURE_DIRECTORY
webby-model-draft run --config CONFIG --plan PLAN --repo CAPTURE_DIRECTORY --output NEW_PRIVATE_DIRECTORY
```

Images are review-only: at most four distinct PNG/JPEG paths, 4 MB per file and 8 MB combined, no side above 8192 pixels and no image above 16 million pixels. Use viewport captures or bounded detail captures for long pages. Paths stay inside the explicit capture root; hidden files, credential-like names, and symlinks are rejected. Screenshots can contain private information even when their filenames look ordinary, so capture only the intended page. The runner checks file structure and dimensions, then sends the validated bytes using the provider's native image input. It does not fetch image URLs or give the selected model tools. Unsupported images/models fail without a text-only substitute. `review_proposed` cannot be combined with images because an unrendered source proposal has no matching pixels.

Image reviews include explicitly selected `context_files` as supplemental capture data. Text-only comprehension reviews omit brief/context to avoid feeding the desired answer to the reader. Text evidence must always quote the job's primary `path`; screenshot observations belong in `visual_observations`.

An accepted image review requires `image_access: "viewed"` and at least one location-specific observation for every attachment. Each observation has `image`, `location`, `observation`, and `recommendation`. The receipt records image path, type, dimensions, byte count, SHA-256, and `image_transport`, alongside requested/reported model and usage. Provider resizing/tokenization may affect perception; image access is model-reported, so assess the observations against the actual captures. Changed source or screenshot bytes invalidate the run. A successful result evaluates those captured states and does not establish interaction behavior, contrast compliance, live search performance, or a guaranteed design quality score.

## Accepting output

The output directory contains `receipt.json`, `changes.patch`, and proposed source files when the plan succeeds. Review jobs add structured findings to the receipt. Validate the exact artifact paths reported by the program; do not assume a patch exists after failure. A failed plan can retain completed-job receipts for diagnosis but must not be applied as a completed plan. Provider refusals, truncation, missing credentials, boundary violations, and unexpected model IDs are actionable failures.

The evidence quotes in a reader result must occur in the supplied text. This catches fabricated quotations; Webby must still assess whether the claim follows from the quote and whether the underlying business fact is true. For a stronger check, compare the target reader with an independent model and the owner-grounded fact sheet. Repeat live searches only within the selected service's supported access and agreed usage; record date, query, model/service, cited URL, and failures without turning a small sample into a ranking forecast.
