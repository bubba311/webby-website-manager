---
name: webby-model-choice
description: Coordinate owner-selected Codex and Claude Code website tasks through an isolated companion runner, or prepare a plan when the runner is not connected.
---

# Let the owner choose the coding agent

Offer a simple choice when the owner asks: “Use Codex for the whole site,” “Have Claude Code make the FAQ,” or “Let Webby choose.” Codex and Claude Code are coding agents, not interchangeable model IDs. Their contribution is a creative and workflow choice. Do not claim that a page ranks or gets cited better because it was written by the same model that later reads it.

Keep the normal Webby path: a short brief, a reviewable branch and pull request, relevant site checks, and owner-controlled publishing. The website still needs clear facts, strong visual design, descriptive structure and links, and a working main action regardless of which agent writes it.

## Choose a scope

For one agent to make the whole site, assign that agent the site's file tree, such as `site/**`. For a split, ask the owner only which meaningful part each agent owns if their request does not say. Describe the assignments in plain words first. Use one short task per step and explicit repo-relative file patterns. Do not let agents overwrite each other's work silently; steps run in order and later steps can see earlier work. Put shared design direction, true company facts, and the visitor action in the plan brief.

The optional companion runner accepts JSON plans with `brief` and `steps`, each containing `agent` (`codex` or `claude`), `task`, and `paths`. See `docs/MODEL_CHOICE.md` for the format and setup. It makes a disposable local clone and returns a patch; the owner’s GitHub checkout and credential store are not mounted into the coding-agent container. Inspect the patch and apply it to Webby's branch only after verifying file scope and content. Run site checks and then use `webby-github` to open the PR. A generated patch is never publication approval.

## Check availability before promising a run

The present Plow cloud Webby does not have this companion runner, Docker, or the owner's Codex/Claude Code subscriptions connected. Do not attempt to start either coding agent in the Plow container, which holds GitHub authentication. Do not ask anyone to paste account tokens into chat. If an isolated companion has been installed by the operator, use `webby-model-runner doctor codex` or `webby-model-runner doctor claude` there to check the selected runner, subscription login, and Codex sandbox. Only promise delegation to agents that report ready. The companion also checks those conditions before every plan. If unavailable, create the scoped JSON plan and explain the exact missing connection or sandbox condition; continue with Webby's normal website workflow if the owner wants progress now. Never label Webby-authored work as Codex- or Claude-authored.
