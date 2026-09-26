# Design decisions

Use for a new composition or a substantial visual redesign. Scale the work to the brief; a small copy fix does not require a new art direction. These are working defaults and review criteria, not a single house style.

## Direction before decoration

- Decide what the visitor should understand, believe, and do. Put the offer, audience, and next action in visible words. Sequence supporting material around real questions: what it does, why it fits, how it works, evidence, limitations, next step. Add only the sections that earn their place.
- Translate the brand into concrete choices. An editorial direction might use oversized display type, an asymmetric grid, disciplined rules, and generous margins; a technical product might use compact diagrams and precise labels; a service business might rely on original photography and a warm reading rhythm. Do not transplant Webby's own palette or composition into every customer site.
- Choose a memorable visual device that belongs to the business: type composition, an original illustration, a product demonstration, an image crop, or a recurring structural detail. Reserve high contrast and visual complexity for important moments. Generic gradient blobs, equal-weight card grids, fake dashboard art, excessive pills, and decorative badges are not a substitute for a concept.
- Keep interaction conventions recognizable even when the composition is experimental. Navigation, links, forms, and the next action should remain easy to identify. Distinctive art direction does not require novel controls.

## Layout and visual hierarchy

- Establish a small set of shared alignment lines and responsive page gutters. Use grid or flex relationships rather than isolated coordinates. Align headlines, text, figures, and actions intentionally; optical corrections are useful when curves or glyph shapes make mathematically equal edges look uneven.
- Give the page one dominant starting point, then a clear reading sequence. Use size, weight, placement, contrast, and whitespace together. If every section shouts, reduce secondary emphasis before making the hero larger.
- Make related elements visibly closer than unrelated groups. Use named spacing tokens for details, components, and section boundaries; a 4px or 8px rhythm is a useful starting point, not a reason to preserve awkward gaps. More whitespace is useful only when the relationships remain clear.
- Vary composition when the content warrants it: a broad statement, a close product detail, a compact comparison, a quiet answer. Avoid giving every section identical height, background, or card structure. Keep repeated components consistent.
- Let DOM order follow the intended reading and keyboard sequence. Do not use CSS reordering to make a desktop layout whose meaning breaks on mobile or in an accessibility tree.

## Typography, color, and imagery

- Set roles for display, section heading, body, navigation, label, and caption. Choose a small type scale and consistent weights. One good family can be enough; add a second only for a clear role. Preserve owner-supplied brand fonts and licenses.
- Start ordinary body and navigation text around 16–18 CSS px, then judge the actual font and audience. This is a readability default, not a universal conformance threshold. Do not shrink header links or body text to rescue an overcrowded composition.
- For paragraphs, start around 45–75 characters per line and line height near 1.5–1.7. Adjust for typeface, language, and content. Display headlines can be tighter and shorter; check their actual line breaks at every width. Use fluid sizing with sensible bounds and relative units; avoid viewport-only text sizing that defeats zoom.
- Assign palette roles: canvas, surface, text, muted text, accent, border, and feedback. Evaluate the actual foreground/background pairing, including image overlays and hover/focus states. Normal text needs at least 4.5:1 contrast; large text (at least 24px regular or about 18.7px bold) needs 3:1. Required control boundaries and state indicators need 3:1 against adjacent colors. Color alone must not carry meaning.
- Use supplied product evidence and honest artwork. Mark a conceptual mockup as an illustration when it could be mistaken for real results. Keep essential statements as text, give meaningful images useful alternatives, and use empty alternatives for decoration. Reserve dimensions to prevent image and font loading from moving the page.

## Responsive behavior and interaction

- Choose breakpoints when content stops fitting, not just for named devices. Let columns stack without losing their relationships. Keep reading widths bounded on large displays; preserve comfortable gutters on small ones. Fix an overflow cause rather than hiding the entire page's horizontal overflow.
- Use links for navigation and buttons for actions, with clear visible names. Keep the same label for the same action. Expose expanded, selected, busy, invalid, and disabled states correctly. Use native controls before custom widgets.
- Aim for comfortable touch targets around 44×44 CSS px. At minimum, satisfy 24×24 CSS px or the applicable spacing/inline exception. Retain visible keyboard focus and keep it clear of sticky headers, cookie notices, and dialogs. Provide a non-drag alternative for essential dragging interactions.
- Keep essential information and actions available without hover. Ensure menus work with keyboard, touch, and pointer. Dialogs need an accessible name, sensible focus handling, an exit, and focus restoration.
- When a real form is in scope, ask only for information the task requires. Use persistent labels, suitable input types and autocomplete, associated hints, clear required status, field-specific errors, and an announced success or error result. Preserve entered values on failure. Never display a successful submission until the destination accepted it.
- Motion should explain change or direct attention. Prefer brief, purposeful transitions; honor reduced-motion preferences. Do not hide core content until an animation or scroll effect runs. Avoid moving targets, scroll hijacking, and hover-only reveals. Provide pause controls when continuing motion requires them.

## Speed and trustworthy content

- Make the main content available promptly. Size images for their rendered use, provide responsive sources when useful, and defer offscreen media. Do not lazy-load the hero image that supplies the main content. Avoid adding heavy animation or client JavaScript for an effect achievable with ordinary HTML/CSS.
- Use available licensed local fonts or a system stack; add new external assets only within the owner's scope. Limit font weights, provide fallbacks, and check layout shifts. Keep interactions responsive by avoiding long synchronous work and unnecessary third-party code.
- Keep important facts in crawlable, readable page content: names, offering, eligibility, location when relevant, real prices/units, limitations, and contact options. Put supporting evidence near factual claims. Match metadata and structured data to the visible page. Do not fabricate quotes, scarcity, customer counts, badges, or endorsements for visual polish.
- When several models contribute, give each the same approved facts, audience, page outline, voice, component rules, and section boundary. Integrate into one coherent page. Authorship alone does not demonstrate that a particular search or browsing system will favor the text.
