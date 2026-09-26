# Rendered review

Use this after a new site or substantial visual change. For a small change, check the affected component and its nearest responsive states. Use the available browser/preview tools; do not claim a check that was not run. A screenshot supports visual inspection, not complete accessibility conformance or real-user performance.

## Packaged browser capture

When `webby-render-check` is installed, use it to collect actual browser evidence before visual review:

```sh
install -d -m 700 /var/lib/plow/models
webby-render-check https://example.com --output /var/lib/plow/models/site-review-001
```

On an existing installation where the command is absent from `PATH`, use `node /var/lib/plow/workspace/skills/webby-model-choice/webby-render-check` with the same arguments. Create the private artifact parent as the current runtime user; do not change another user's state ownership.

For a locally running approved preview, add `--allow-loopback` and give its exact URL, for example `http://127.0.0.1:4173`. Choose a new absolute output directory outside source repositories; the parent directory must exist. The helper captures 320, 375, 768, and 1440px views plus reduced motion, saves screenshots and visible page text, and records accessibility-tree and keyboard-focus samples in `manifest.json`. Open the screenshot files with the available image-reading tool and inspect the evidence. Do not just repeat the helper's measurements as a design judgment.

The helper uses fresh browser contexts, imports no login, restricts networking, and never clicks or submits controls. Blocked resources, truncation, or script failures are recorded and can limit the result. Its measurements identify candidates for inspection; overflow may be intentional, a focus style alone does not prove visibility, and a keyboard sample is not a completed visitor task. Complete the relevant manual steps below with an interactive browser where available. If that access is missing, report task execution as unverified.

To have another model check comprehension, pass the artifact directory as the read-only input to the model review workflow, selecting the saved `*-text.txt` visible text and `*-accessibility.txt` snapshot. Keep the same factual questions and expected answers across models. Do not grant source-edit access for a comprehension review, or claim a model examined screenshots unless that runner actually supports image input.

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
