# Webby Website Manager

Webby is a multiplayer OpenClaw agent for startup websites. A teammate requests a change in Plow Chat; Webby makes it in an owner-approved GitHub repository, opens a pull request, checks the preview, and reports back. The site owner controls publishing. The image inherits Plow's OpenClaw starter, group chat, and Agent Index usage reporter.

## What is here

- `Dockerfile`: a small variant of the pinned [Plow OpenClaw base image](https://github.com/plow-pbc/plow-openclaw-agent).
- `prompt/AGENTS.md`: Webby's role and multiplayer rules.
- `skills/webby-github/SKILL.md`: the first real website workflow.
- `compose.yml`: local Plow development with a loopback dashboard.
- `.github/workflows/image.yml`: remote Docker build for computers without Docker; publishing is a separate manual dispatch.

## Connect and run locally

You need Docker Engine and Compose 2.24+, the [Plow CLI](https://github.com/plow-pbc/plow-agents), and a Plow phone line. From this directory:

```sh
plow-agents login
plow-agents lines
plow-agents deploy --local --line LINE_UID
docker compose ps
```

Text the line shown by `plow-agents lines`. The local dashboard is at `http://localhost:3001`; it is an owner-admin interface and should stay on loopback. The image uses Plow's model provider, so a separate model API key is not required for this route. To use GitHub locally, set `GH_TOKEN` in a private `.env` file or export it for Compose. Use a token scoped only to the selected website repositories.

In an owner-only chat, tell Webby which `OWNER/REPO` is the website. Webby records approved repositories in `/var/lib/plow/webby-approved-repos`. Request a small change in a group chat to exercise the multiplayer workflow.

## Build without local Docker

The GitHub Action validates the image on pushes and pull requests. A manual `workflow_dispatch` with `publish=true` pushes a `ghcr.io/OWNER/REPO:webby-SHA` image. Make the GHCR package public before asking Plow to deploy it. Do not put tokens in the image. After signing in to Plow, the owner can use `plow-agents image push` or a published digest with `plow-agents deploy IMAGE@sha256:DIGEST --line LINE_UID`.

For the hackathon, Webby's image sets `AGENT_ID=webby-website-manager`, so the inherited reporter registers and sends real usage to the [Agent Index](https://aiworthusing.com/agent-index/publish). Submission still needs a public MIT repository, a working image, a 60-second demo, and verification by the organizers. The submission deadline is September 28, 2026 at 11:59 p.m. PT.

## First live test

1. Connect GitHub in the owner-only Plow conversation. Do not send a token in chat.
2. Approve one website repository, preferably a GitHub site that deploys previews for pull requests.
3. In a group with another person, request a small real change such as correcting a CTA or updating a launch date.
4. Confirm Webby returns a pull request and a working preview. Approve and merge only after review, then have Webby verify the live page.

Webby currently operates GitHub-backed sites. Webflow, Framer, and Wix adapters are planned after this workflow has real users.
