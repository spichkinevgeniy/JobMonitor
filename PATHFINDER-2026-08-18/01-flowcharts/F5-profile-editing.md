# F5 — Редактирование профиля поиска (три транспорта)

## Транспорт 1 — бот: ничего не пишет

`cmd_settings` (`settings.py:27`) и `open_settings_from_profile` (`:42`) только
читают через `UserService.get_user_by_tg_id` и рисуют меню. Ни один из трёх
обработчиков не пишет в `users`.

Но бот решает главное — **куда попадёт пользователь**, и раздаёт кнопки в
разные модели записи (`app/telegram/bot/views/settings.py:32-45`):

```
SETTINGS_ENTRY_SPECIALTY: "react/" если MINIAPP_REACT_ENABLED иначе "specialty"
SETTINGS_ENTRY_FORMAT:    "format"   ← всегда легаси
SETTINGS_ENTRY_SALARY:    "salary"   ← всегда легаси
SETTINGS_ENTRY_LEVEL:     "level"    ← всегда легаси
```

**При включённом флаге одно меню из четырёх кнопок отдаёт пользователю две
несовместимые модели записи одновременно.** Сейчас на проде флаг выключен,
поэтому проблема спит.

## Транспорт 2 — легаси: прямая запись в активный профиль

`save_specialty` (`routes.py:229`), `save_format` (`:267`), `save_salary`
(`:310`), `save_level` (`:357`) → `UserService.update_profile_*`
(`user_service.py:113,129,145,175`). Каждый берёт `get_by_tg_id_for_update`,
меняет поля и коммитит. **Немедленно, по одному полю, без черновика.**
`onboarding_draft` не трогает никогда.

Списки вариантов строятся из полных перечислений и защищены проверкой на
импорте (`page_context.py:219-241`).

## Транспорт 3 — React: черновик, перенос только на «завершить»

`GET /onboarding` → `get_state`; если черновика нет, он синтезируется из живого
профиля (`onboarding_service.py:171`). `PATCH /draft` пишет **только**
`onboarding_draft`. `POST /complete` → `_apply_completed_draft`
(`:137`) переносит в `cv_*` и обнуляет черновик.

`onboarding_draft` — JSONB-колонка **той же строки** `users`
(`models.py:70`). Обе модели пишут одну строку, разные колонки.

## Где транспорты расходятся

| Поле | Легаси | React |
|---|---|---|
| специализации и навыки | сразу, полные перечисления | через черновик, **урезанные клиентом** |
| формат работы | `set_legacy_work_format` — **один** | `set_work_formats` — **несколько** |
| зарплата | сразу | на `/complete` |
| режим грейда | любой из четырёх | только `EXACT`, либо `AT_LEAST` для `JUNIOR_PLUS` |
| опыт | пишется (`user_service.py:164-170`) | **не пишется никогда** |
| `Grade.LEAD` | выбирается | недостижим |

## Четыре сценария порчи данных

Все достижимы из **одного и того же меню бота**.

1. Легаси сохраняет `Mobile` и `Kotlin`. Пользователь открывает React-кнопку —
   значения приходят с сервера, но отбрасываются фильтром, следующий `PATCH`
   сохраняет усечённый набор, `/complete` затирает `cv_*`. **Тихая потеря.**
2. Незавершённый React-черновик + правка зарплаты через легаси → возврат в
   React и «завершить» **откатывает правку**.
3. React выставил два формата работы, легаси-кнопка формата схлопывает их в
   один. Вернуть множественность можно только заново пройдя React.
4. `/complete` жёстко ставит `filter_grade_mode = EXACT`. У пользователя,
   чей профиль собран из резюме (там `UP_TO`), фильтр молча сужается, а опыт
   остаётся замороженным — React его не трогает.

## Урезание списков подтверждено с точными числами

| | В React зашито | В домене | Разница |
|---|---|---|---|
| специализации | **6** (`SpecialtyStep.tsx:24-61`) | **9** (`value_objects.py:43-52`) | нет DS/ML, Mobile, GameDev |
| навыки | **7** (`SpecialtyStep.tsx:63-71`) | **40** (`value_objects.py:55-112`) | **33 недостижимы** |

Фильтрация — **жёсткий отброс, а не скрытие в интерфейсе**, в трёх точках:
`mappers.ts:66-67`, `SpecialtyStep.tsx:81-88`, `SearchProfileForm.tsx:54-55`.
Отфильтрованный массив уходит обратно на сервер через
`specialtyDraftRequest` (`mappers.ts:78-85`). Бэкенд принимает полные
перечисления на обоих транспортах — сужение целиком на стороне клиента, и оно
**уничтожает серверные данные на круговом обходе**.

## Два канала initData

| Запрос | Канал |
|---|---|
| легаси GET | заголовок `X-Telegram-Init-Data` (`app.js:305`) |
| легаси POST | **поле `init_data` в теле** (`app.js:257`) |
| React, всё | только заголовок (`createTelegramBaseQuery.ts:23-28`) |

Оба приходят в один `validate_init_data`. Легаси-канал означает, что
подписанные данные попадают в тела запросов и логи на записи, но в заголовки
на чтения.

## Схема

```mermaid
flowchart TD
  A1["/settings<br/>app/telegram/bot/routers/settings.py:27"] --> A3["send_settings_menu, только чтение<br/>app/telegram/bot/settings_menu.py:14"]
  A3 --> A6["_entry_to_page<br/>app/telegram/bot/views/settings.py:32"]
  A6 -->|specialty при флаге| R1["React ?mode=settings<br/>frontend/apps/shell/src/app/App.tsx:36"]
  A6 -->|format, salary, level всегда| L1["легаси-страницы<br/>app/telegram/miniapp/routes.py:113,122,131"]
  L1 --> LJ2["POST, init_data в теле<br/>app/telegram/miniapp/static/js/app.js:251"]
  LJ2 --> U1["update_profile_*<br/>app/application/services/user_service.py:113,129,145,175"]
  U1 --> DB["users: cv_* и filter_*<br/>app/infrastructure/db/mappers/user.py:77"]
  R1 --> R3["SearchProfileForm<br/>.../SearchProfileForm.tsx:128"]
  R3 --> R5["GET /onboarding<br/>app/telegram/miniapp/onboarding_routes.py:24"]
  R5 --> R7["_draft_from_active_profile, полные перечисления<br/>app/application/services/onboarding_service.py:171"]
  R7 --> F1["onboardingStateToDraft — ФИЛЬТР 9 в 6 и 40 в 7<br/>.../features/onboarding/api/mappers.ts:63"]
  F1 --> F3["обратно уходит усечённый набор<br/>.../features/onboarding/api/mappers.ts:78"]
  F3 --> R9["PATCH /draft<br/>app/telegram/miniapp/onboarding_routes.py:32"]
  R9 --> DBD["users.onboarding_draft JSONB<br/>app/infrastructure/db/models.py:70"]
  R3 --> R12["POST /complete<br/>app/telegram/miniapp/onboarding_routes.py:41"]
  R12 --> R14["_apply_completed_draft, черновик обнуляется<br/>app/application/services/onboarding_service.py:137"]
  R14 --> DB
  RR["импорт резюме пишет черновик<br/>app/application/services/resume_import_service.py:131"] --> DBD
  DBD -.->|переносится только через complete| DB
  U1 -.->|конфликт: затирается устаревшим черновиком| R14
```

## Пробелы

Шаблоны Jinja не читались — фильтрация на уровне шаблона не проверена, хотя
проверка на импорте делает её маловероятной. Уровень изоляции транзакций при
одновременных легаси-POST и React-PATCH не подтверждён. Тесты
`mappers.test.ts` могут фиксировать урезание как ожидаемое поведение — не
проверено.
