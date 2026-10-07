# UI direction: Rosch

Reference: https://www.rosch.in/ (reviewed 7 October 2026).

## Observed source characteristics

The website's HTML and CSS were inspected directly after the web reader could not access it. This is a source-based review, not a rendered-browser or animation review.

- White background with dark charcoal foreground (`--background: 0 0% 100%`, `--foreground: 225 7% 12%`).
- Neue Montreal regular typography, supplied as a local font.
- Compact work/about/contact navigation and an off-canvas menu.
- Studio introduction, recent work, and visual project presentation.
- Source includes video controls, magnetic-item styling, and a custom cursor component; their actual rendered behavior was not verified.

## Proposed adaptation for the analyst

Use the monochrome palette, strong typographic hierarchy, generous spacing, restrained borders, and concise navigation as the visual direction. Translate the work-focused presentation into a data-focused workspace:

1. Header: application name and clear workspace navigation.
2. Introduction: one concise statement and the upload action.
3. Dataset panel: filenames, row counts, profile status, and preview links.
4. Main analysis area: question input, readable result tables, charts, and collapsible query details.
5. Feedback: clear progress, empty states, per-file errors, and clarification prompts.

These are proposed design choices, not claims that the reference implements this application layout. Use an available system sans-serif initially; do not copy its font files, branding, imagery, or video assets. Keep native cursor behavior, keyboard access, visible focus, readable contrast, and reduced-motion support. Large decorative motion would interfere with inspecting tables and charts.

Applied to the shared header/footer, workspace, dataset preview, profile tables, and planning form. The interface now uses a white/charcoal palette, large editorial headings, restrained separators, generous spacing, and responsive stacked sections. Local system fonts are used. File submission, CSRF protection, session ownership, and planning behavior are preserved. Planning still returns JSON; calculated results and a conversation interface remain later milestones.

Verification: 55 backend/template tests pass, Django checks pass, and static assets collect successfully. Browser visual verification has not been performed in this environment.
