# JobMonitor Frontend

React-интерфейс Telegram Mini App для настройки профиля поиска вакансий в JobMonitor.

Этот каталог содержит только frontend-часть проекта. Документация backend, базы данных, Telegram-бота и инфраструктуры находится в корне репозитория и в корневом `docs/`.

## Стек

- React 19
- TypeScript
- Vite
- Material UI
- Emotion
- Inter (`@fontsource/inter`)
- Storybook
- Playwright — для автоматизированного visual audit

Frontend организован как npm workspace. Приложения находятся в:

```text
frontend/apps/shell
frontend/apps/dashboard
```

## Быстрый запуск

Из каталога `frontend`:

```bash
npm ci
npm run dev:shell
```

Vite запустит shell-приложение в dev-режиме.

Production build:

```bash
npm run build:shell
```

Storybook:

```bash
npm run storybook
```

## Структура

```text
frontend/
├── apps/
│   ├── shell/
│       ├── design/              # HTML entrypoints design previews
│       ├── src/
│       │   ├── app/             # bootstrap приложения и theme
│       │   ├── pages/           # страницы
│       │   ├── features/        # пользовательские сценарии
│       │   ├── shared/          # общие API, Telegram helpers и UI
│       │   └── design/          # preview-компоненты для UI-аудита
│       ├── index.html
│       └── vite.config.ts
│   └── dashboard/          # кабинет зарегистрированного пользователя
├── packages/              # общие UI, API и Telegram-модули
├── docs/
│   ├── ARCHITECTURE.md
│   └── DESIGN_SYSTEM.md
├── package.json
└── package-lock.json
```

Подробно:

- [Архитектура frontend](docs/ARCHITECTURE.md)
- [Design system](docs/DESIGN_SYSTEM.md)

## Основной пользовательский сценарий

Сейчас shell реализует onboarding из четырёх шагов:

```text
Specialty
   ↓
Work Format
   ↓
Salary
   ↓
Level
```

Данные между шагами собираются в draft внутри переиспользуемой feature `SearchProfileForm`. Страницы onboarding и settings задают сценарное поведение.

Пользователь может вернуться на уже посещённый шаг через `ProgressStepper`. Переход на ещё не посещённые шаги блокируется.

## Telegram Mini App

При старте приложение пытается получить `window.Telegram.WebApp`.

Если Telegram WebApp доступен:

- вызываются `ready()` и `expand()`;
- `initData` используется для авторизованных запросов frontend → backend;
- запросы через `telegramGet` передают `X-Telegram-Init-Data`.

В обычном браузере frontend должен оставаться пригодным для локальной разработки и design previews.

## Design previews

Для shared UI и onboarding-композиций существуют отдельные preview pages.

Примеры:

```text
/miniapp/react/design/button/index.html
/miniapp/react/design/chip/index.html
/miniapp/react/design/text-field/index.html
/miniapp/react/design/specialty-step/index.html
```

Они нужны для:

- проверки компонента вне production-сценария;
- демонстрации состояний компонента;
- автоматического visual audit;
- сравнения React-реализации с Figma baseline.

Preview-код не должен импортироваться production-приложением.

## Visual audit

В frontend используется автоматизированный pipeline сравнения React и Figma.

Основные команды:

```bash
npm run visual:capture
npm run visual:compare
npm run visual:test
npm run visual:verify
```

`visual:capture` собирает текущие React-снимки и manifest.

`visual:compare` сравнивает React-артефакты с зарегистрированными Figma baseline.

`visual:test` выполняет capture и compare последовательно.

`visual:verify` проверяет, что comparator действительно падает на намеренно испорченном baseline.

> Имена npm scripts должны быть записаны без обратного слеша: `visual:test`, а не `visual\:test`.

Подробный `VISUAL_TESTING.md` стоит зафиксировать после завершения текущей универсализации collector и DOM-контракта, чтобы не документировать промежуточную схему.

## Правила разработки

1. Не помещайте переиспользуемые UI-компоненты прямо в `pages`.
2. Пользовательский сценарий относится к `features`.
3. Базовые UI-примитивы, API-клиент и Telegram helpers относятся к `shared`.
4. Design preview должен использовать production-компонент, а не отдельную копию его разметки.
5. Не импортируйте код из `design/` в production-слои.
6. Новые визуальные значения сначала оформляйте как design tokens, если они повторяются.
7. Не связывайте frontend напрямую с деталями backend-реализации: граница проходит через `shared/api`.

## Backend

Backend намеренно не описан в этой документации.

Frontend знает о серверной части только через API-контракт. Документацию endpoint-ов и полный integration flow имеет смысл добавлять отдельно, когда frontend/backend интеграция будет стабилизирована.
