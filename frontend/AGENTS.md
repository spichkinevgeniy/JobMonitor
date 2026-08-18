# JobMonitor Frontend

React and TypeScript workspace containing the JobMonitor Telegram Mini Apps and
their shared packages.

This file applies to everything inside `frontend/`. Follow the repository root
`AGENTS.md` as well. When a more specific `AGENTS.md` exists closer to the code
being changed, follow that file for area-specific behavior.

## General Guidelines

- Do not modify code unrelated to the current task.
- Follow existing frontend conventions before introducing a new pattern.
- Prefer simple, explicit code over premature abstractions.
- Do not add dependencies without a concrete requirement.
- Do not edit generated `dist` files manually.
- Preserve the boundaries between Mini Apps and shared packages.

## Workspace

```text
frontend/
├── apps/
│   ├── shell/                   # Onboarding and search profile settings
│   └── dashboard/               # Active profile, search status and vacancies
└── packages/
    ├── ui/                      # Cross-app reusable UI
    └── telegram/                # Telegram-specific utilities
```

Public production paths:

```text
apps/shell       → /miniapp/react/
apps/dashboard   → /miniapp/dashboard/
backend API      → /miniapp/api/
```

## Stack

- React 19
- TypeScript
- Vite
- MUI
- RTK Query

Use the libraries and patterns already established in the workspace. Do not
introduce an alternative UI library, data-fetching library, router, or state
manager without a concrete need.

## Application Boundaries

`apps/shell` and `apps/dashboard` are separate Mini Apps.

- Do not import implementation details directly between applications.
- Do not duplicate Dashboard UI inside Shell.
- Do not duplicate Shell business features inside Dashboard.
- Cross-app reusable UI belongs in `@jobmonitor/ui`.
- Telegram-specific frontend utilities belong in `@jobmonitor/telegram`.
- Shared code must have a real cross-app use case before it is moved into a
  package.
- Keep application-specific composition and behavior inside the owning app.

Prefer public package entry points. Do not reach into another package's
internal source directories unless that path is an explicitly supported public
API.

## Frontend Architecture

Applications follow an FSD-like structure:

```text
src/
├── app/
├── pages/
├── features/
├── entities/
└── shared/
```

Responsibilities:

- `app` configures application-wide providers, initialization and entry points.
- `pages` compose complete user scenarios.
- `features` own reusable user-facing business behavior.
- `entities` contain reusable domain representations and entity-specific logic.
- `shared` contains generic UI, utilities, configuration and infrastructure
  without application business rules.

Do not create every possible layer preemptively. Add a layer, abstraction, or
shared module only when the current task provides a concrete use case.

Avoid circular dependencies and imports from higher-level layers into
lower-level layers. Keep public APIs explicit when a feature or entity exposes
code to the rest of an application.

## React Conventions

- Keep state as close as possible to the component or feature that owns it.
- Do not store a value in state when it can be derived during rendering.
- Do not define React components inside other components.
- Put user-interaction logic in event handlers rather than effects.
- Use effects only to synchronize React with an external system.
- Keep effect dependencies accurate; do not suppress dependency warnings to
  force a desired execution pattern.
- Use functional state updates when the next value depends on the previous
  value.
- Do not add `useMemo`, `useCallback`, or `React.memo` automatically. Use them
  when referential stability or an expensive operation creates a concrete need.
- Run independent asynchronous operations in parallel when their ordering does
  not matter.
- Handle loading, empty and error states explicitly for asynchronous UI.

## State and Data Fetching

Use RTK Query for backend server state, request lifecycle and cache
invalidation.

- Do not duplicate RTK Query response data in a Redux slice.
- Do not copy server data into local state unless the user is editing an
  intentionally independent draft.
- Keep temporary unsaved form state inside the feature that owns the form.
- Do not add a Redux slice, Zustand store, Context-based store, or another
  global container unless state must genuinely be shared beyond its owner.
- Define cache tags and invalidation according to the affected backend
  resources.
- Keep Telegram authentication header handling in shared API infrastructure,
  not in individual components.

Telegram init data is passed through:

```text
X-Telegram-Init-Data
```

Do not duplicate init data inside request bodies.

## UI Conventions

- Prefer MUI and existing `@jobmonitor/ui` components.
- Use the existing theme for colors, typography, spacing and breakpoints.
- Do not introduce isolated raw design values when an appropriate theme token
  already exists.
- Keep generic reusable components in `@jobmonitor/ui`.
- Keep business-specific UI inside the owning feature or application.
- Preserve accessible labels, focus behavior, keyboard navigation and visible
  focus states.
- Design for Telegram WebView viewport constraints, not only desktop browser
  dimensions.

Do not move a component into `@jobmonitor/ui` merely because it is visually
reusable. Components coupled to search profiles, vacancies or onboarding
remain domain or feature components.

## Telegram Mini App Environment

- Test affected flows inside real Telegram WebViews in addition to desktop
  browser testing.
- Account for Telegram theme and viewport behavior where the existing
  integration supports it.
- Keep Telegram-specific browser and SDK utilities in `@jobmonitor/telegram`.
- Do not scatter direct Telegram SDK access throughout pages and components
  when an existing shared abstraction covers the use case.

Telegram iOS WebView has special keyboard and viewport behavior. Reusable
focused-input scrolling logic belongs to the feature that owns the form, not
to individual input steps.

## Routing and Production Builds

Nginx serves the frontend production builds and proxies backend requests.

- Do not change a Vite `base` path without checking the corresponding Nginx
  route.
- Do not assume development-server routing matches production routing.
- Preserve trailing-slash behavior expected by the deployed Mini App URLs.
- Verify assets load correctly from the application's production base path.
- Do not commit generated build output unless the repository explicitly tracks
  it and the task requires regeneration.

The Shell currently selects its onboarding/settings scenario through URL query
parameters. Do not add a routing library solely for that flow unless routing
requirements grow beyond the current approach.

## Development Workflow

Before finishing frontend changes, run the relevant available scripts defined
by the affected workspace packages:

1. Targeted tests while iterating.
2. The broader relevant test suite.
3. Type checking.
4. Linting.
5. The relevant production build.

When a shared package changes, verify every affected consuming application.
Report checks that could not be run and the reason they were unavailable.

## Area-Specific Instructions

More specific behavior belongs in nested files when needed:

- `apps/shell/AGENTS.md` — onboarding, settings, search profile drafts, resume
  import and form-specific WebView behavior.
- `apps/dashboard/AGENTS.md` — active search profile, status, vacancies and
  Dashboard navigation.

Keep this file limited to conventions shared across the frontend workspace.