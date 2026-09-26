---
name: webby-create
description: Turn a short owner brief into a polished static startup website, prepare a reviewed GitHub pull request, and publish through GitHub Pages after owner approval.
---

# Create a startup website

Use this when the owner wants a new website and does not yet have a site repository. Keep the path from brief to review short. Use `webby-github` for authentication, repository approval, branches, pull requests, and publication.

## Get the few facts that matter

From the owner's brief, identify the company name, what it offers, who it is for, and the one action visitors should take. Use a supplied email or URL for that action. Ask one concise follow-up only for facts needed to make the page truthful or the contact action work. Choose a distinctive visual direction from the brief; the owner can refine colors and copy in the pull request. Do not invent customers, results, prices, team biographies, testimonials, legal claims, or contact details. Omit a section when there is no honest content for it. Handle page structure and discoverability as part of the build; do not make the owner learn technical terms or fill out a separate checklist.

If the owner has a repository already, use the approved repository rather than creating another. A new repository must be requested in the owner's direct conversation. Confirm the GitHub owner/account and a short repository name from context; if ambiguous, ask. On GitHub Free, Pages requires a public repository. Explain that before creating the repository if the owner expected its source to stay private. Keep the repository on the approved list only after the owner has authorized it.

## Build the draft

Find the starter at `/opt/webby/starter-site`. On an existing cloud installation, use `/var/lib/plow/workspace/skills/webby-create/starter-site` if the first path is absent. Copy its contents into a new or approved repository on a `webby/...` branch. For a new repository, initialize `main` with a README first so the site can arrive as a pull request. Work in `$WEBBY_SITES_DIR/OWNER/REPO`; never edit the default branch directly.

Replace every `data-template` field with specific, owner-grounded copy and remove the attribute. Make the company, offer, audience, and next action understandable from the visible page without relying on artwork. Use a descriptive page title, useful summary, one clear headline, meaningful section headings, and links or buttons whose names describe their actions. Keep those facts consistent between visible copy and page metadata. Set the canonical URL, social metadata, contact destination, and `site/sitemap.xml` to the real site URL. Replace the starter README with a short project README naming the company, live URL, and how to edit the site. Keep asset URLs relative so the page works at a project-site path such as `https://OWNER.github.io/REPO/`. The starter's abstract artwork is decorative; adapt its colors in `site/styles.css` if the brief suggests a direction. Do not add external fonts, analytics, forms, or scripts unless requested. GitHub Pages hosts static files; a real submission form, sign-in, payment flow, or database needs another service.

Run `python3 scripts/check_site.py` before opening the pull request. It checks the page structure, metadata, sitemap, local links and assets, and whether visible actions have names; fix failures instead of asking the owner to do the technical work. Preview the site locally at desktop and mobile widths. Check keyboard focus, the real destinations of external links, and whether the final words answer what the company does, for whom, and what happens next. The script cannot judge whether a claim is true or whether an outside URL works. If essential facts are still missing, leave the branch as a draft and tell the owner exactly which facts are needed; do not publish placeholders. Open a pull request with the page URL that will be used, a short explanation of the design, screenshots or a verified preview if available, and check results in plain language. GitHub Pages does not provide a pull-request preview automatically.

## Publish with owner control

The starter workflow checks pull requests and deploys only from `main` after the owner approves and merges the site pull request. The repository's Pages source must be **GitHub Actions**. As part of an owner-authorized launch, check `gh api repos/OWNER/REPO/pages`; if Pages is absent, try `gh api -X POST repos/OWNER/REPO/pages -f build_type=workflow`. If it already exists with another source, try `gh api -X PUT repos/OWNER/REPO/pages -f build_type=workflow`. If permissions or plan limits prevent this, give the owner the exact one-time path: **Settings → Pages → Build and deployment → Source → GitHub Actions**. Do not ask them to do that step when Webby can complete it. The default project-site URL is `https://OWNER.github.io/REPO/`; a repository named `OWNER.github.io` instead uses the root URL. A custom domain requires separate Pages and DNS setup, so do not claim it is connected until verified.

After merge, inspect the workflow run and open the live URL. Report the live link only if it works and displays the approved copy. If Pages setup or deployment fails, report the exact missing setting or error. Later edits follow the same branch → pull request → owner merge → live verification path.
