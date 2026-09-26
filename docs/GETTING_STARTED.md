# Get Webby running

[← Back to Webby](../README.md) · [Website](https://bubba311.github.io/webby-website-manager/) · [Agent Index](https://aiworthusing.com/agent-index/webby-website-manager)

Webby creates and updates GitHub-backed websites through Plow Chat. It opens code changes as pull requests for your review. Its live-site check is read-only until you ask it to fix something.

## Cloud setup

One-click installation is pending on the Agent Index. The cloud route below works now and does not require local Docker or a separate model key.

1. Install the [Plow CLI](https://github.com/plow-pbc/plow-agents), sign in by text, and find an available phone line:

   ```sh
   git clone https://github.com/plow-pbc/plow-agents.git
   cd plow-agents
   ./bin/plow-agents login
   ./bin/plow-agents lines
   ```

2. Replace `LINE_UID` with an available line ID from the previous command, then deploy the current Webby image:

   ```sh
   ./bin/plow-agents deploy ghcr.io/bubba311/webby-website-manager@sha256:4ea4277008ed87501251285aff38d6a1e92986a9e4167358e6dc201906f18d24 --line LINE_UID
   ./bin/plow-agents agents
   ```

3. When its status is `running`, text the number shown by `./bin/plow-agents lines`. In your direct chat with Webby, say “Connect GitHub.” Webby gives you a code for [GitHub device login](https://github.com/login/device). After approving it, text “Check GitHub connection.” GitHub CLI's browser authorization has account-level OAuth scopes; Webby applies its approved-repository list when deciding what to edit.

4. If you need a site, text “Create a website for my startup. Ask me only for its name, what it does, and where the main button should go. Open a pull request for review; don't publish it yet.” Webby will ask for the few details it cannot infer and create a GitHub-backed site draft. If you already have a website repository, say “Approve `OWNER/REPO` as my website repository,” then ask for a focused change. Review the PR before publishing. For a team workflow, ask Webby to create a trusted group with your teammates after you decide who should have access.

Webby's own [website](https://bubba311.github.io/webby-website-manager/) lives in this repository's `site/` folder, so it is also a real site Webby can edit. [PR #1](https://github.com/bubba311/webby-website-manager/pull/1) documents its first site change.

## Audit agent access

Text Webby: “Audit my approved website for search access and browser-agent usability. Show the evidence and top three fixes. Don’t edit yet.” It checks the live page and its origin-level crawl rules, then separates observable issues from checks that need a search or analytics account. Each finding includes the URL, what Webby observed, why it matters, and a specific fix. Ask “Fix the first issue in a PR” when you want code changes; Webby leaves publishing to the owner.

You can run the same read-only audit locally with Python 3:

```sh
python3 scripts/webby-site-audit https://your-public-site.example/
python3 scripts/webby-site-audit https://your-public-site.example/ --format json
```

The audit checks what a public page serves and how its controls are labeled. It does not measure search placement or whether third-party assistants use the page. Webby treats crawler permissions as an owner decision.

## What is here

- `Dockerfile`: a small variant of the pinned [Plow OpenClaw base image](https://github.com/plow-pbc/plow-openclaw-agent).
- `prompt/AGENTS.md`: Webby's role and multiplayer rules.
- `skills/webby-github/SKILL.md`: the first real website workflow.
- `skills/webby-create/SKILL.md` and `starter-site/`: create a first website from a short brief, then review it as a pull request.
- `skills/webby-audit/SKILL.md` and `scripts/webby-site-audit`: evidence-based live-site access and usability checks.
- `compose.yml`: local Plow development with a loopback dashboard.
- `.github/workflows/image.yml`: remote Docker build for computers without Docker; publishing is a separate manual dispatch.
- `.github/workflows/site.yml`: checks the static site's links and assets on pull requests.
- `.github/workflows/pages.yml`: publishes site changes after a reviewed pull request is merged to `main`.
- `site/`: Webby's own startup website, which is the first site to manage.

## Develop locally

You need Docker Engine and Compose 2.24+, the [Plow CLI](https://github.com/plow-pbc/plow-agents), and a Plow phone line. From this directory:

```sh
plow-agents login
plow-agents lines
plow-agents deploy --local --line LINE_UID
docker compose ps
```

Text the line shown by `plow-agents lines`. The local dashboard is at `http://localhost:3001`; it is an owner-admin interface and should stay on loopback. The image uses Plow's model provider, so a separate model API key is not required for this route. To use GitHub locally, set `GH_TOKEN` in a private `.env` file or export it for Compose. Use a token scoped only to the selected website repositories.

Webby returns a device-login code from `webby-github-login start`; approve it at `https://github.com/login/device`, then ask Webby to check the connection. Webby records approved repositories in `/var/lib/plow/webby-approved-repos`. Request a small change in a group chat to exercise the multiplayer workflow.

## Build without local Docker

The GitHub Action validates the image on pushes and pull requests. A manual `workflow_dispatch` with `publish=true` pushes a `ghcr.io/OWNER/REPO:webby-SHA` image. Make the GHCR package public before asking Plow to deploy it. Do not put tokens in the image. After signing in to Plow, the owner can use `plow-agents image push` or a published digest with `plow-agents deploy IMAGE@sha256:DIGEST --line LINE_UID`.

For the hackathon, Webby's image sets `AGENT_ID=webby-website-manager`, so the inherited reporter registers and sends real usage to the [Agent Index](https://aiworthusing.com/agent-index/publish). Submission still needs a public MIT repository, a working image, a 60-second demo, and verification by the organizers. The submission deadline is September 28, 2026 at 11:59 p.m. PT.

## Verify a new integration

1. Connect GitHub in the owner-only Plow conversation. Do not send a token in chat.
2. Approve one website repository, preferably a GitHub site that deploys previews for pull requests.
3. In a group with another person, request a small real change such as correcting a CTA or updating a launch date.
4. Confirm Webby returns a pull request and a working preview. Approve and merge only after review, then have Webby verify the live page.

Webby currently operates GitHub-backed sites. Webflow, Framer, and Wix adapters are planned after this workflow has real users.

## Webby's own website

The static site in `site/` can be previewed with `python3 -m http.server 8000 --directory site` and opened at `http://localhost:8000`. GitHub Pages is configured with GitHub Actions as its source. Merging a reviewed pull request that changes `site/` deploys the new site automatically; the workflow can also be run manually. This is a real site for Webby's first pull-request test; the site itself does not require a framework or a separate hosting account.
