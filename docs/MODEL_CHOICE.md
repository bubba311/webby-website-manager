# Choose who writes each part

Ask Webby: **“Use Codex for the hero, Claude for the product details, and check whether Gemini understands the finished page.”** You can also choose one model for the whole site. Webby prepares the assignments, combines the drafts with the site's visual system, runs its checks, and opens a pull request for review.

Connect only the providers you want to use. Your subscription or provider account pays for those calls under its own limits. Selecting a writer is separate from testing a reader: a comprehension check can reveal unclear facts, but it does not measure whether a search service will discover or recommend your site.

Custom model connections are optional for ordinary design review: Webby can use its host's configured vision model to inspect screenshots. If you choose a different reviewer, Webby can send the same captured page to your connected vision-capable model and record its visual findings.

## Available connections

| Connection | Access | What Webby can request |
| --- | --- | --- |
| Codex CLI | ChatGPT subscription sign-in | Drafts, reading checks, and screenshots with an available image-capable model. |
| Claude Code CLI | Claude subscription sign-in | Drafts, reading checks, and native screenshot reviews with supported models. |
| OpenAI | API key | Drafts and reviews through Responses, including supported image input. |
| Anthropic | API key | Drafts and reviews through Messages, including supported image input. |
| Google Gemini | API key | Drafts and reviews through `generateContent`, including supported image input. |
| OpenAI-compatible service, including OpenRouter | That service's API key and configured HTTPS endpoint | Drafts and reviews through compatible chat completions; images require endpoint/model support. |

A model must be available through the chosen account and interface. API profiles accept arbitrary supported model IDs; Codex uses the installed CLI's known model catalog so its tool-free configuration can be verified. A newer Codex model can require a CLI update. Compatibility is checked at the request and response level. Webby reports missing access, unsupported output, refusals, and model mismatches instead of silently choosing a substitute. An intentional alias can be allowed and the provider-reported model is recorded when available.

## Connect once

The published image includes the model programs. From a local checkout, the standalone commands need Python 3.10+, plus the relevant provider CLI for subscription calls. The tested CLI versions are Codex 0.157.1 and Claude Code 2.1.281. Direct API calls need no coding CLI or Docker.

Initialize private state on the machine running Webby:

```sh
python3 scripts/webby-model-connect init
```

This prints the configuration path. Locally it defaults to `~/.local/share/webby/models/config.json`; in Webby's cloud image it is `/var/lib/plow/models/config.json`. It preserves existing configuration. Login directories and key files stay outside website repositories.

For Codex, ask Webby **“Connect Codex.”** It runs the device-login command and gives you the official browser URL and short code. Complete the provider's login and ask Webby to check the connection. The same commands work in a terminal:

```sh
python3 scripts/webby-model-connect login codex
python3 scripts/webby-model-connect status codex
```

For Claude Code, complete its browser flow from a private interactive terminal on the machine running Webby:

```sh
python3 scripts/webby-model-connect login claude
python3 scripts/webby-model-connect status claude
```

If the provider returns an authorization code, enter it in that terminal, not in chat. Claude's browser callback and API-key entry need private terminal access; a hosting plan that exposes only chat cannot complete those connections through this helper yet. Codex device login works through an owner chat. Existing local CLI users may point a subscription profile's `auth_dir` to their local login directory, or omit it to use the current CLI login; do not copy that login into a different user's installation.

For API access, use the hidden key prompt in a private terminal. Replace `openai` with `anthropic`, `gemini`, or `openrouter` as appropriate:

```sh
python3 scripts/webby-model-connect key openai
```

Keys are saved in private files with mode 600. Alternatively, configure a provider profile to name a secret environment variable supplied by your host. Never paste keys in chat, put them in a command argument, or commit them. Use the provider's own account settings for spending limits. Save a preferred available model so Webby does not ask on every request:

```sh
python3 scripts/webby-model-connect prefer openai YOUR_AVAILABLE_MODEL_ID
```

Check a connection without making a paid generation call:

```sh
python3 scripts/webby-model-draft doctor --config /absolute/path/to/config.json --provider openai
```

This checks configuration and credential availability. The first successful draft or reader check verifies actual model access.

## What happens to the website

Webby sends only the relevant files or sections, the brief, and explicitly selected supporting context. It retains the actual website checkout and controls integration. Model jobs return source proposals or reading reports; generated code is not executed as part of drafting. Separate sections in the same HTML file can go to different writers, while a whole-site assignment enumerates the source files that model should draft.

The result includes proposed files, a patch, and a receipt recording requested models, provider-reported model information when available, usage, and outcomes. Webby reviews the combined design and facts, applies the accepted patch to a working branch, and performs the site's build and rendered checks before review. Failed or incomplete plans are not presented as finished work. A failed call can still consume provider usage; Webby does not automatically rerun an entire plan. Direct API requests have output-token limits. Codex CLI has bounded elapsed time and captured output size but does not expose the same hard token cap; its own network layer can retry internally. These differences are recorded rather than treated as identical billing controls.

Claude's CLI output-token setting is advisory: in a live test, reported output including thinking exceeded the requested value. Its CLI budget setting is also provider-enforced, so account spending controls remain useful. Webby's own hard limits for both CLIs are elapsed time and captured output size.

Screenshot review sends explicit captured images alongside visible text using native image inputs. The selected model receives no browser or file-editing tools. Its receipt includes exact image hashes, provider/model evidence, usage, and observations tied to locations in each screenshot. An unavailable image model fails clearly; Webby does not call a text-only response a visual pass. Captured pixels reveal layout and typography, while actual browser actions still need separate interaction checks.

The [plan reference](../skills/webby-model-choice/references/plans.md) documents the command interface for developers. Everyday users can keep asking Webby in plain language.
