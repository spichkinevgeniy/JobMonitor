# Frontend Design System

Документ описывает текущие правила UI в JobMonitor frontend.

Основная цель design system — не просто хранить цвета и кнопки, а не допускать расхождения между Figma, shared-компонентами и production-экранами.

## 1. Технологическая основа

UI построен на:

- Material UI;
- Emotion/styled API;
- Inter;
- собственных primitive и semantic tokens.

Глобальная тема создаётся в:

```text
apps/shell/src/app/theme/theme.ts
```

Токены находятся в:

```text
apps/shell/src/app/theme/foundations.ts
```

## 2. Шрифт

Основной шрифт:

```text
Inter
```

В entrypoint приложения подключены веса:

```text
400
500
600
700
```

MUI theme:

```text
fontFamily: Inter, sans-serif
```

Если компонент неожиданно рендерится через Arial/system font, это нужно считать сигналом для проверки inheritance/preview target, а не новой нормой design system.

## 3. Primitive colors

Текущая палитра:

| Token | Value |
|---|---|
| `color/blue/50` | `#EFF6FF` |
| `color/blue/100` | `#DBEAFE` |
| `color/blue/500` | `#3B82F6` |
| `color/blue/600` | `#2563EB` |
| `color/blue/700` | `#1D4ED8` |
| `color/neutral/0` | `#FFFFFF` |
| `color/neutral/50` | `#F7F8FA` |
| `color/neutral/100` | `#F2F4F7` |
| `color/neutral/200` | `#E4E7EC` |
| `color/neutral/400` | `#98A2B3` |
| `color/neutral/500` | `#667085` |
| `color/neutral/700` | `#344054` |
| `color/neutral/900` | `#101828` |
| `color/green/600` | `#16A34A` |
| `color/red/600` | `#DC2626` |

## 4. Semantic colors

Production-компоненты должны по возможности использовать semantic token вместо прямого primitive hex.

### Background

| Token | Value |
|---|---|
| `color/bg/default` | `#F7F8FA` |
| `color/bg/surface` | `#FFFFFF` |
| `color/bg/subtle` | `#F2F4F7` |
| `color/bg/primary-subtle` | `#EFF6FF` |
| `color/bg/primary` | `#2563EB` |
| `color/bg/primary-hover` | `#1D4ED8` |
| `color/bg/disabled` | `#E4E7EC` |

### Text

| Token | Value |
|---|---|
| `color/text/primary` | `#101828` |
| `color/text/secondary` | `#667085` |
| `color/text/tertiary` | `#98A2B3` |
| `color/text/inverse` | `#FFFFFF` |
| `color/text/brand` | `#2563EB` |
| `color/text/disabled` | `#98A2B3` |

### Border

| Token | Value |
|---|---|
| `color/border/default` | `#E4E7EC` |
| `color/border/strong` | `#98A2B3` |
| `color/border/brand` | `#2563EB` |
| `color/border/disabled` | `#E4E7EC` |

### State

| Token | Value |
|---|---|
| `color/state/success` | `#16A34A` |
| `color/state/error` | `#DC2626` |

### Icon

| Token | Value |
|---|---|
| `color/icon/brand` | `#2563EB` |
| `color/icon/secondary` | `#667085` |
| `color/icon/disabled` | `#98A2B3` |
| `color/icon/inverse` | `#FFFFFF` |

## 5. Shape

Базовый radius MUI theme:

```text
12px
```

Он подходит для основных cards, inputs и primary controls.

Локальные исключения допустимы, если это часть спецификации компонента:

- navigation/icon controls: `8px`;
- pills/chips: полный pill radius;
- step circles: `50%`.

Не нужно механически ставить `12px` на каждый элемент.

## 6. Touch targets

Интерактивные элементы mobile UI должны сохранять удобную область нажатия.

Текущие ориентиры:

```text
primary button     48px height
back button        44px height
icon button        44 × 44px
step hit area      около 44 × 44px
```

Визуальный элемент может быть меньше touch target. Например circle stepper может иметь диаметр 28px, но кликабельная область — 44px.

## 7. Shared UI

Текущие базовые компоненты:

```text
shared/ui/
├── BackButton/
├── Button/
├── Chip/
├── IconButton/
├── ProgressStepper/
├── SelectionCard/
└── TextField/
```

### Button

Используется для primary action.

Основные свойства текущего дизайна:

```text
min-height: 48px
radius: 12px
font: Inter 16 / 600
horizontal padding: 20px
primary: #2563EB
hover: #1D4ED8
```

Компонент также имеет disabled и loading states.

### BackButton

Навигационное действие назад.

```text
height: 44px
radius: 8px
font: Inter 14 / 500 / 20
brand color: #2563EB
```

Содержит leading chevron icon.

### IconButton

Квадратный icon-only control.

```text
44 × 44px
radius: 8px
icon: 20px
```

Обязателен доступный `aria-label`, если смысл кнопки не выражен видимым текстом.

### SelectionCard

Интерактивная карточка выбора.

Поддерживает:

- default;
- selected;
- hover/focus;
- disabled.

Карточка может содержать leading icon, title, description и selected indicator.

### Chip

Компактный pill для коротких значений/skills.

Типовая высота:

```text
32px
```

Для текстовых chips важны точные content insets и состояние selected/disabled.

### TextField

Общий text input.

Поддерживает:

- label;
- placeholder;
- helper text;
- error;
- disabled;
- start/end adornment;
- input mode.

Внешний `FormControl` и визуальная рамка input — разные DOM-уровни. Это важно для design preview и visual audit: baseline должен быть привязан к тому уровню, который реально сравнивается с Figma.

### ProgressStepper

Отображает прогресс onboarding.

Поддерживает:

- completed;
- active;
- upcoming;
- переход к уже посещённому шагу.

Нельзя давать пользователю перейти к шагу, который ещё не был открыт.

## 8. Где можно использовать MUI напрямую

MUI layout primitives можно использовать в feature/page для композиции:

```text
Box
Stack
Typography
```

Но если появляется повторяющийся интерактивный control с собственными состояниями и стилями, его следует вынести в `shared/ui`.

Плохо:

```text
каждый экран создаёт собственную primary button через <MuiButton sx={...}>
```

Хорошо:

```text
экраны используют один shared/ui/Button
```

## 9. Storybook и Design Preview — разные задачи

### Storybook

Используется для:

- документации props;
- ручного просмотра states;
- проверки поведения;
- accessibility-oriented development;
- компонентных сценариев.

### Design Preview

Используется для:

- стабильного deterministic render;
- screenshot capture;
- visual audit;
- сравнения с Figma;
- проверки геометрии и visual tokens.

Design Preview не заменяет Storybook, Storybook не заменяет Visual Audit.

## 10. Figma → React

Рекомендуемый flow:

```text
Figma component
   ↓
stable audit ID
   ↓
shared/ui implementation
   ↓
Design Preview
   ↓
React capture
   ↓
Figma baseline comparison
```

Нельзя подгонять production CSS под случайный screenshot artefact, если structured metrics уже совпадают.

Особенно это касается различий rasterization текста между Figma и Chromium.

При сравнении сначала проверяются:

1. geometry;
2. colors;
3. typography;
4. spacing;
5. raster.

## 11. Правило добавления нового UI-компонента

Перед добавлением компонента ответьте на вопросы:

1. Он используется или потенциально будет использоваться больше чем в одном месте?
2. У него есть самостоятельные visual states?
3. Он является design-system primitive, а не частью одного конкретного feature?
4. Есть ли соответствующий компонент/паттерн в Figma?

Если да — создавайте в:

```text
shared/ui/<ComponentName>/
```

Минимальная структура:

```text
ComponentName/
├── ComponentName.tsx
├── ComponentName.types.ts
├── ComponentName.stories.tsx
└── index.ts
```

Если компонент участвует в visual audit, добавьте отдельный deterministic design preview.

## 12. Изменение дизайна

Если изменение намеренное:

```text
1. обновить Figma
2. обновить/зарегистрировать baseline
3. обновить React component
4. запустить visual capture
5. запустить comparator
6. проверить diff
```

Не обновляйте baseline только для того, чтобы сделать тест зелёным.

Baseline означает «это новый утверждённый дизайн», а не «это текущее случайное состояние кода».

## 13. Что не относится к design system

В design system не нужно переносить:

- API-запросы;
- Telegram integration;
- управление onboarding draft;
- backend DTO;
- page navigation;
- feature-specific validation.

Design system отвечает за визуальные примитивы и их поведение, а не за бизнес-flow.
