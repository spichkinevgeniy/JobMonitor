# JobMonitor — Agent Guidelines

## Project

JobMonitor is a Telegram bot and Telegram Mini App for vacancy monitoring.

The project consists of:
- Telegram bot
- FastAPI backend
- PostgreSQL
- React + TypeScript Telegram Mini App

## Frontend

The new Mini App is located in:

frontend/apps/shell

Stack:
- React 19
- TypeScript
- Vite
- MUI

Frontend architecture is FSD-like:

src/
- app/
- pages/
- features/
- entities/
- shared/

Do not introduce Redux, Zustand or another global state manager for the
onboarding flow unless there is a concrete requirement.

Search profile form state is owned by the reusable
`features/search-profile-form` business feature. `OnboardingPage` is the thin
page-level integration boundary.

## Onboarding

The new onboarding consists of four steps:

1. Specialty and skills
2. Work formats
3. Salary
4. Level and summary

The onboarding is intended for new bot users.

The backend must use an explicit onboarding completion state.
Do not infer onboarding completion from individual filter values.

Planned source of truth:

user.onboarding_completed_at

NULL:
- onboarding is required

non-NULL:
- onboarding has already been completed

Existing users created before introduction of the new onboarding must not be
forced through onboarding.

## Onboarding API

Do not make the new React onboarding depend on the four legacy form endpoints.

Legacy endpoints currently represent the old HTML forms and may remain
temporarily for backwards compatibility.

The new React onboarding should eventually submit the complete draft through
one endpoint:

POST /miniapp/api/onboarding

Telegram initData should be passed through:

X-Telegram-Init-Data

rather than duplicated inside every request body.

## Telegram Mini App

The React build is served under:

/miniapp/react/

The frontend must be tested inside the real Telegram iOS WebView, not only in a
desktop browser.

The onboarding layout uses:
- fixed-height flex root
- non-scrolling header
- internal scrollable content
- persistent footer

Do not replace this with position: fixed without a concrete reason.

## iOS keyboard

Telegram iOS WebView has special keyboard/viewport behavior.

Reusable logic for keeping focused inputs visible lives in the search profile
form feature lib.

Do not duplicate this logic inside individual steps.

SalaryStep and SpecialtyStep use the same focused-input scroll behavior.

## SelectionCard

SelectionCard is shared between onboarding steps.

Changes to specialty-card layout must not unintentionally change
WorkFormatStep or SalaryStep.

Specialty cards use a dedicated vertical layout because two-column cards have
less horizontal space.

## Development

Before finishing frontend changes, run the available:
- typecheck
- lint
- build

Do not edit generated dist files manually.
