# Frontend Architecture

Документ описывает архитектуру React-части JobMonitor. Backend и инфраструктура здесь рассматриваются только как внешние зависимости.

## 1. Общая схема

Frontend находится в npm workspace:

```text
frontend/
└── apps/
    └── shell/
```

`shell` — текущее React-приложение Telegram Mini App.

Упрощённый runtime flow:

```text
main.tsx
   ↓
ThemeProvider + CssBaseline
   ↓
App
   ↓
Telegram WebApp initialization
   ↓
OnboardingPage
   ↓
Specialty → Work Format → Salary → Level
```

Сейчас отдельный client-side router для onboarding не требуется: `App` напрямую рендерит `OnboardingPage`.

## 2. Слои

Внутри `apps/shell/src` используется FSD-подобное разделение:

```text
src/
├── app/
├── pages/
├── features/
├── shared/
└── design/
```



### `app`

Содержит глобальную инициализацию приложения.

Текущие обязанности:

- корневой `App`;
- MUI theme;
- design tokens;
- глобальные provider-ы.

Примеры:

```text
app/App.tsx
app/theme/foundations.ts
app/theme/theme.ts
```

`app` может собирать нижележащие слои, но бизнес-логику отдельных сценариев сюда переносить не нужно.

### `pages`

Страница собирает законченный пользовательский экран/flow из features и shared-компонентов.

Сейчас основная страница:

```text
pages/onboarding/OnboardingPage.tsx
```

`OnboardingPage` отвечает за:

- текущий шаг;
- общий draft onboarding;
- максимальный посещённый шаг;
- переходы вперёд/назад;
- навигацию к уже посещённым шагам;
- сбор финального результата.

Страница не должна содержать стили и внутреннюю реализацию базовых UI-компонентов.

### `features`

Feature — законченный пользовательский сценарий или его существенная часть.

Сейчас:

```text
features/onboarding/
├── lib/
└── ui/
    ├── SpecialtyStep/
    ├── WorkFormatStep/
    ├── SalaryStep/
    └── LevelStep/
```

Каждый step:

- получает initial value;
- хранит локальное состояние, относящееся только к своему экрану;
- валидирует пользовательский ввод;
- отдаёт нормализованное значение наружу через callback;
- не управляет всем onboarding flow самостоятельно.

Оркестрация четырёх шагов остаётся в `OnboardingPage`.


### `shared`

`shared` не знает о конкретном пользовательском сценарии.

Текущие области:

```text
shared/
├── api/
├── lib/
│   └── telegram/
└── ui/
```

`shared/api`:

- общий transport;
- API errors;
- добавление Telegram init data к запросам.

`shared/lib/telegram`:

- доступ к `window.Telegram.WebApp`;
- `ready()`;
- `expand()`;
- проверка Telegram environment.

`shared/ui`:

- Button;
- BackButton;
- IconButton;
- SelectionCard;
- Chip;
- TextField;
- ProgressStepper.

### `design`

`src/design` и HTML entrypoints в `apps/shell/design` — development-only слой.

Он используется для:

- изолированного просмотра UI;
- deterministic visual states;
- visual regression/audit;
- сопоставления React с Figma.

Production-код не должен зависеть от `design`.

## 3. Направление зависимостей

Основное правило:

```text
app
 ↓
pages
 ↓
features
 ↓
shared
```

Допустимые зависимости:

```text
app      → pages, features, shared
pages    → features, shared
features → shared
shared   → shared
```

Нежелательные зависимости:

```text
shared   → features
shared   → pages
features → pages
production → design
```

## 4. Onboarding state

Текущее состояние onboarding централизовано в `OnboardingPage`:

```ts
interface OnboardingDraft {
  specialty: SpecialtyId | null
  skills: Skill[]
  workFormats: WorkFormatId[]
  salary: SalaryStepValue
  level: LevelId | null
}
```

Flow:

```text
Step 1
SpecialtyStepValue
   ↓
draft.specialty + draft.skills
   ↓
Step 2
WorkFormatStepValue
   ↓
draft.workFormats
   ↓
Step 3
SalaryStepValue
   ↓
draft.salary
   ↓
Step 4
LevelStepValue
   ↓
CompletedOnboardingValue
```

`maxVisitedStep` хранит самый дальний шаг, до которого пользователь уже дошёл.

Это позволяет:

- вернуться назад;
- открыть уже посещённый шаг;
- не перепрыгнуть на ещё не посещённый шаг.

### Когда нужен глобальный state manager

Пока onboarding живёт в одном page-flow, локальный React state остаётся достаточным.

Redux Toolkit/Zustand имеет смысл добавлять только если данные onboarding понадобятся одновременно:

- нескольким независимым страницам;
- нескольким приложениям;
- долгоживущим несвязанным компонентам;
- сложному persistence/synchronization flow.

Не нужно переносить локальный draft в глобальный store только ради самого факта использования Redux.

## 5. Telegram boundary

`App` вызывает инициализацию Telegram WebApp при mount.

```text
App
 ↓
initializeTelegramWebApp()
 ↓
window.Telegram?.WebApp
 ↓
ready()
expand()
```

Код, завязанный на Telegram platform API, должен оставаться в:

```text
shared/lib/telegram
```

Feature/page не должны напрямую размазывать обращения к `window.Telegram` по компонентам.

## 6. API boundary

Запросы frontend не должны знать детали backend-классов, ORM или внутренних сервисов.

Текущий transport:

```text
feature/page
   ↓
shared/api
   ↓
fetch
   ↓
HTTP API
```

Для Telegram-authorized запросов `telegramGet` получает `initData` и передаёт:

```text
X-Telegram-Init-Data
```

Если API станет больше, рекомендуется развивать слой `shared/api` или выделять entity/feature API-модули, а не писать `fetch()` непосредственно внутри UI-компонентов.

## 7. UI composition

Правило:

```text
page
  собирает feature

feature
  собирает shared/ui

shared/ui
  реализует reusable visual primitive
```

Пример:

```text
OnboardingPage
   ↓
SpecialtyStep
   ↓
ProgressStepper
SelectionCard
Chip
Button
BackButton
```

Страница управляет flow, step — пользовательским сценарием, shared-компоненты — визуальным и интерактивным поведением.

## 8. Design previews

Каждый переиспользуемый UI-компонент должен иметь изолированный preview, если для него важны визуальные состояния.

Vite собирает preview pages как отдельные HTML entrypoints.

Примеры:

```text
design/button/index.html
design/chip/index.html
design/text-field/index.html
design/progress-stepper/index.html
```

Preview должен:

- рендерить настоящий production-компонент;
- показывать важные states;
- иметь стабильные данные;
- не зависеть от backend;
- не менять production API только ради демонстрации без необходимости.

## 9. Path alias

Для импортов внутри shell используется alias:

```ts
@/...
```

Он указывает на:

```text
apps/shell/src
```

Предпочтительно:

```ts
import { Button } from '@/shared/ui/Button'
```

вместо глубоких относительных импортов:

```ts
import { Button } from '../../../../shared/ui/Button'
```

## 10. Как добавлять новую frontend-фичу

Перед добавлением кода определите ответственность.

Если это новый экран:

```text
pages/<page>
```

Если это пользовательское действие или сценарий:

```text
features/<feature>
```

Если это переиспользуемая бизнес-сущность:

```text
entities/<entity>
```

Если это универсальный UI/lib/API helper:

```text
shared/...
```

Если это только development preview:

```text
design/...
```

Главный критерий — не название папки, а направление зависимостей и зона ответственности.
