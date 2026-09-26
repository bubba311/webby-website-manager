# Rendered review

Use this after a new site or substantial visual change. For a small change, check the affected component and its nearest responsive states. Use the available browser/preview tools; do not claim a check that was not run. A screenshot supports visual inspection, not complete accessibility conformance or real-user performance.

## Packaged browser capture

When `webby-render-check` is installed, use it to collect actual browser evidence before visual review:

```sh
install -d -m 700 /var/lib/plow/models
webby-render-check https://example.com --output /var/lib/plow/models/site-review-001
```

On an existing installation where the command is absent from `PATH`, use `node /var/lib/plow/workspace/skills/webby-model-choice/webby-render-check` with the same arguments. Create the private artifact parent as the current runtime user; do not change another user's state ownership.

For a locally running approved preview, add `--allow-loopback` and give its exact URL, for example `http://127.0.0.1:4173`. Choose a new absolute output directory outside source repositories; the parent directory must exist. The helper captures 320, 375, 768, and 1440px views plus reduced motion, saves screenshots and visible page text, and records accessibility-tree and keyboard-focus samples in `manifest.json`. Open the screenshot files with the available image-reading tool and inspect the evidence. If the current model cannot inspect image pixels, use the connected model review below. Do not just repeat the helper's measurements as a design judgment.

The helper uses fresh browser contexts, imports no login, restricts networking, and never clicks or submits controls. Blocked resources, truncation, or script failures are recorded and can limit the result. Its measurements identify candidates for inspection; overflow may be intentional, a focus style alone does not prove visibility, and a keyboard sample is not a completed visitor task. Complete the relevant manual steps below with an interactive browser where available. If that access is missing, report task execution as unverified.

## Use a connected model to inspect the screenshots

When no particular reviewer was chosen and Webby runs on Plow, prefer its configured native image capability. Check the installed CLI's help and model configuration for an available image-capable model, then make a bounded request using the actual screenshot:

```sh
openclaw infer image describe --file CAPTURE_DIRECTORY/375-viewport.png --model CONFIGURED_VISION_MODEL --prompt 'Inspect this actual website screenshot for visual hierarchy, typography, spacing, alignment, and readable actions. Ground observations in visible locations. Separate material defects from optional taste. This is a viewport capture: content continuing below its bottom edge is normal. State what this image cannot establish.' --json
```

Fill the path and model from the current installation; do not hardcode a model that may be unavailable elsewhere. Use the CLI's configured authentication, without extracting or repurposing internal tokens. Check the returned success, image capability, reported model, and image-specific observations. Record the screenshot path/SHA-256, capture context, requested/reported model, and returned result in the private review evidence. Inspect the response before deciding whether another view needs a request. This route reuses the existing installation and does not require a new writer account.

If the owner chose a reviewer, preserve that choice. Use `webby-model-choice` for that selected connection, or when the native route is unavailable and an approved connected vision model is suitable. Stay within existing account and usage permissions. Follow [plans and receipts](../../webby-model-choice/references/plans.md) for connection checks, plan validation, invocation, and installation fallbacks. Handle the mechanics; do not ask the owner to assemble files or choose a model again when an approved suitable choice exists.

Set `--repo` to the private capture directory, not the website source checkout. Use a review-only plan with visible text, accessibility context, and actual screenshots from the same rendered state. For example, fill `CONNECTED_PROFILE` and `EXACT_VISION_MODEL_ID` from the verified connection before validating this plan:

```json
{
  "version": 1,
  "brief": "Review this website against the approved business brief and visual direction. Identify material improvements from the supplied evidence.",
  "context_files": ["1440-accessibility.txt", "375-text.txt"],
  "jobs": [{
    "id": "visual-review",
    "provider": "CONNECTED_PROFILE",
    "model": "EXACT_VISION_MODEL_ID",
    "operation": "review",
    "path": "1440-text.txt",
    "images": ["1440-viewport.png", "375-viewport.png", "1440-page.png", "375-page.png"],
    "task": "Inspect every attached screenshot. Assess hierarchy, typography, spacing, alignment, identity, and responsive composition. Ground each observation in a named image and visible location. Use the supplied text for factual context. Distinguish material defects from optional taste; report unreadable or missing evidence. Do not infer interaction success or search placement."
  }]
}
```

Run `webby-model-draft validate --config CONFIG --plan PLAN --repo CAPTURE_DIRECTORY`, then `webby-model-draft run --config CONFIG --plan PLAN --repo CAPTURE_DIRECTORY --output NEW_PRIVATE_REVIEW_DIRECTORY`. Screenshot paths are explicit relative paths beneath the capture directory. Select up to four PNG/JPEG images, at most 4 MB each and 8 MB combined, with neither dimension above 8192px or more than 16 million pixels per image. If a page is longer, use focused section viewport captures in separate reviews; record which portions were inspected. Do not silently omit a failed image. Render an edited proposal before reviewing it; screenshot jobs cannot use `review_proposed`.

Read the completed receipt and review artifact. Accept only a `review_ready` result with accepted jobs, `image_access: "viewed"`, and image-specific `visual_observations`. Preserve the image SHA-256 hashes, requested model, reported model when available, and image transport in the review evidence. These identify the submitted pixels and model response; the model reports its own inspection. Check whether its observations actually refer to visible details, and distinguish inference from direct evidence. A text-only response, unavailable vision model, or failed image request leaves visual review unverified; it must not become a visual pass. Follow the existing connection workflow if one-time access is missing.

For either route, a viewport screenshot ends at the fold. Compare suspected clipping with the full-page capture, truncation flag, and DOM bounds before calling it a layout defect. Low-resolution details or an uninspected section remain uncertain. Do not silently replace the owner's selected reviewer with another model, treat a generated description as an independently proven fact, or turn a failed image review into a text-only visual verdict.

For comprehension alone, use `*-text.txt` and `*-accessibility.txt` without images and label the result a supplied-text check. Keep factual questions and expected answers consistent across models. Neither screenshot critique nor supplied-text review executes a browsing task, measures live discovery, or supplies an objective aesthetic grade.

## Prepare evidence

1. Start the project's normal preview with the real base path, load the page, and wait for fonts and critical images. Use a local copy or authorized test environment for task execution. Identify the main visitor task, such as understanding the product then opening its signup destination.
2. Capture the first viewport and full page at a representative desktop width (about 1440px) and phone width (about 375px). Inspect both images, not merely their existence. Check 320px, an intermediate width around 768px, and a wide desktop for layout failures; capture additional views when they reveal a problem. Test the actual mobile navigation state.
3. Record the URL/commit, browser, viewport, checked states, and what remains unverified in the review or pull request. Keep screenshots as review artifacts rather than adding bulky generated files to the site unless requested.

## Evaluate the composition

Inspect in this order, fixing the most consequential problem first:

- **Immediate comprehension:** Is the business, audience, and next action clear from the first view? Is a poetic headline supported by concrete copy? Can a visitor distinguish a real action from decorative interface art?
- **Hierarchy:** Is there one clear point of entry and a sensible path through supporting material? Do competing accents, oversized labels, or repeated card treatments dilute it?
- **Layout:** Are alignment lines, gutters, section boundaries, image crops, and visual balance intentional? Is whitespace grouping content or creating accidental holes? Look at the full-page rhythm, not only the hero.
- **Type:** Are body and navigation comfortable to read? Check awkward headline wraps, orphaned words, overly long lines, dense paragraphs, inconsistent weights, and labels too small for their role.
- **Identity:** Could the composition plausibly belong to this business without its logo? Does its distinctive device serve the content? Remove visual habits that merely repeat the starter.
- **Responsive coherence:** Does the phone composition feel designed, with a useful reading sequence and clear action? Correct squashed columns, stretched cards, clipped art, collisions, and wasteful vertical gaps.

Compare before and after at the same viewports. A concrete defect warrants another pass; do not perform endless cosmetic changes after the requested outcome is met. For an ambitious redesign, use an independent reviewer when available and give them the brief and screenshots without steering their verdict. Treat visual taste as judgment, not an invented objective score.

## Verify behavior and inclusive use

- Complete the main visitor task with keyboard navigation and named controls. Inspect roles, labels, heading order, field associations, and exposed states in the accessibility tree where available. Test a touch-size viewport. Do not rely only on coordinate clicks or a DOM snapshot.
- Check each actionable destination. Test menus, disclosures, dialogs, and form validation present in the change, including an empty/error/loading/success state when relevant. Stop before any unapproved purchase, live form submission, or other consequential action; use test data and a test endpoint when supplied.
- Check document and visible element bounds for unintended horizontal overflow. Inspect and fix the responsible element. Legitimate two-dimensional content, such as a wide data table, may need its own labeled scroll region.
- Test browser zoom/text enlargement to 200% without lost content or function. Test reflow at a 320 CSS px content width (equivalent to 400% zoom on a 1280px-wide viewport), allowing only genuinely two-dimensional content its necessary scrolling. These are separate checks.
- Apply user text-spacing overrides: line height 1.5×, paragraph spacing 2× font size, letter spacing 0.12em, and word spacing 0.16em. Verify that nothing clips, overlaps, disappears, or becomes unusable; the override is a stress test, not the site's required default styling.
- Measure contrast for actual text/control colors and focus states. Tab through sticky UI and overlays; focused controls must stay visible. Check target spacing and size, non-color cues, reduced motion, and whether essential content survives a failed decoration or delayed asset.
- Run the available automated accessibility tool if present, resolve relevant findings, then retain the manual results. A clean automated scan covers only what that tool can detect. Do not call the whole site compliant based on that scan.

## Verify loading and report clearly

Check for failed assets, console errors, jumps during loading, and unresponsive interactions. When performance tools are available, record the environment and distinguish a development/lab run from actual visitor data. Good real-user targets are LCP ≤2.5s, INP ≤200ms, and CLS ≤0.1 at the 75th percentile, considering mobile and desktop separately. A Lighthouse page-load score does not measure real-user INP or prove those targets are met. If no field data exists, say so; do not install analytics solely to complete this review without authorization.

The review result should briefly state the visual decision, verified viewports and task outcome, checks run, material fixes, and any unresolved limit. If browser access is unavailable, complete the static checks and deliver a reviewable draft with rendered review explicitly pending. Do not describe unseen output as visually verified.
