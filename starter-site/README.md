# Startup website starter

A one-page static site Webby can tailor from a short brief. It uses plain HTML and CSS, relative asset links, and no build dependencies.

## Give Webby the brief

The essentials are a company name, a sentence about the offer, who it helps, and a working contact email or action URL. A logo, colors, product details, and images are optional. Webby can draft the wording from facts you provide; if a section has no factual basis, it should remove that section.

## Customize and review

1. Copy this starter's contents into your website repository.
2. Replace every `data-template` field in `site/index.html` and remove the attribute. Update the title, description, canonical and social URL, contact destination, and `site/sitemap.xml` with the actual public URL. The visual mark and colors can be changed in `site/favicon.svg` and `site/styles.css`.
3. Run `python3 scripts/check_site.py`. It intentionally fails until the demo text and links are replaced.
4. Preview with `python3 -m http.server 8000 --directory site` and visit `http://localhost:8000/`. Review the page at desktop and phone widths, including keyboard navigation.
5. Open a pull request. The workflow checks the content but does not publish a pull request. The owner reviews and merges it.

## Publish with GitHub Pages

Webby can configure GitHub Pages through the repository API during an owner-authorized launch. If that account lacks permission, open **Settings → Pages → Build and deployment** and select **GitHub Actions** as the source. The included workflow publishes `site/` when an approved change is merged into `main`. It can also be run manually from the Actions tab. For a normal repository, the default URL is `https://OWNER.github.io/REPOSITORY/`; for a repository named `OWNER.github.io`, it is `https://OWNER.github.io/`. Use the right URL in the canonical link and sitemap. All asset paths are relative so they work under either path.

On GitHub Free, the repository must be public to use Pages. Pages content is public even when a plan permits a private source repository. A custom domain needs separate Pages and DNS configuration. The site is static: contact links work, but forms, accounts, payments, or databases need an external service. GitHub Pages does not create a preview URL for each pull request.
