# Snack Overflow Copilot instructions

- Read `PRODUCT.md` for confirmed product behavior and `DESIGN.md` for the currently implemented visual system before making frontend changes.
- Preserve the existing React + Vite frontend, Flask API contracts, authentication, authorization, role-specific actions, and live API data. Do not replace real data with examples or mocks.
- Treat the warm-neutral, deep-navy, orange, and green palette described in `DESIGN.md` as a future design direction, not current CSS. Apply it only when the user explicitly requests a visual redesign or palette change.
- Do not alter UI files when a request is limited to Impeccable setup or documentation.
- Impeccable is installed in the user's VS Code profile. In Copilot Chat Agent mode, use its `/impeccable` commands instead of copying a duplicate skill into the workspace.

Useful commands:
- `/impeccable init` — capture or update product context.
- `/impeccable document` — capture the implemented visual system.
- `/impeccable critique <target>` — review a screen or component.
- `/impeccable audit <target>` — check accessibility, responsiveness, and technical UI quality.
- `/impeccable polish <target>` — refine a requested screen or component.
- `/impeccable adapt <target>` — address a requested viewport or device layout.
- `/impeccable live` — iterate against a running local app.
