# Инвентарь фич — SmartJobMonitor

Ветка `feature/resume-import`, 18 августа 2026. Границы проведены по тому,
как система исполняется (от триггера до терминального состояния), а не по
дереву каталогов.

## Фичи

| # | Фича | Точка входа | Слой |
|---|---|---|---|
| F1 | Приём вакансий: скрапинг → зеркало → разбор → сохранение | `app/telegram/scrapper/handlers.py:43` | бэкенд |
| F2 | Подбор и рассылка | `app/application/services/matcher_service.py:31` | бэкенд |
| F3 | Обратная связь по вакансии | `app/telegram/bot/routers/vacancy_feedback.py:95,135,165` | бэкенд |
| F4 | Регистрация и главное меню | `app/telegram/bot/routers/onboarding.py:20` | бэкенд |
| F5 | Редактирование профиля поиска — **три транспорта** | см. ниже | оба |
| F6 | Импорт резюме — **два транспорта** | см. ниже | оба |
| F7 | Дашборд (состояние поиска) | `app/telegram/miniapp/search_profile_routes.py:16` | оба |
| F8 | Аналитика профиля и советы по навыкам | `app/telegram/miniapp/routes.py:153` | оба |
| F9 | Выгрузка вакансий | `app/telegram/miniapp/routes.py:171` | оба |
| F10 | Аккаунт, приватность, удаление данных | `app/telegram/bot/routers/account.py:30,47` | оба |
| F11 | Админская рассылка | `app/telegram/bot/routers/broadcast.py:21` | бэкенд |
| F12 | Инструменты разработчика | `app/telegram/bot/routers/developer.py:38,51` | бэкенд |

## Две фичи с размноженными транспортами

Это главное, что даёт разведка, и на это смотрит вторая фаза.

**F5 — редактирование профиля, три пути к одной строке `users`:**

- бот с диплинками — `app/telegram/bot/routers/settings.py:18`, меню в `app/telegram/bot/settings_menu.py:14`
- легаси-страницы на Jinja — `app/telegram/miniapp/routes.py:103,112,121,130`, запись `:229,267,310,357`
- React-форма — `frontend/apps/shell/src/app/App.tsx:36,39` → `app/telegram/miniapp/onboarding_routes.py:23,31,40`

Модели записи расходятся: легаси пишет **активный профиль** напрямую через
`UserService.update_profile_*`, React пишет **черновик** и переносит его в
профиль только на `/complete`.

**F6 — импорт резюме, два пути с разными терминальными состояниями:**

- бот, синхронно, пишет активный профиль — `app/telegram/bot/routers/resume.py:104`
- мини-апп, асинхронная задача, пишет черновик — `app/telegram/miniapp/resume_import_routes.py:33,58`

Квота списывается в разных точках: бот внутри слота разбора
(`resume.py:210`), мини-апп до постановки в очередь
(`resume_import_service.py:77`).

## Общая инфраструктура — не фичи

| Забота | Где | Замечание |
|---|---|---|
| Запуск процессов | `app/main.py:6`, `app/bot_main.py:17`, `app/bootstrap/*` | **две разные сборки**: `run_application` поднимает бота, скрапер, мини-апп и синхронизацию метрик; `run_bot_component` — только бота и опционально скрапер |
| Авторизация мини-аппа | `app/telegram/miniapp/auth.py:17`, `deps.py:51,58,67` | **два канала initData**: заголовок `X-Telegram-Init-Data` и поле `init_data` в теле (`routes.py:176,233,271,314,361`) |
| Персистентность | `app/infrastructure/db/**`, пять UoW | `vacancy_feedback.py` — единственное место, обходящее слой |
| Доступ к LLM | `app/infrastructure/llm.py`, `llm_runtime.py` | используется F1 и F6 |
| Разбор резюме | `app/infrastructure/parsers/*` | `acquire_parse_slot` — общий шлюз для обоих транспортов F6 |
| Наблюдаемость | `app/infrastructure/observability/*`, `app/bootstrap/metrics_sync.py` | счётчики переживают перезапуск через таблицу |
| Приватность и конфиг | `app/core/{config,logger,privacy}.py` | `user_ref`, `file_ext` — вычистка PII |
| Общие пакеты фронта | `frontend/packages/{ui,telegram}` | тема MUI, обёртка WebApp, базовый запрос RTK |
| Раздача статики | `app/telegram/miniapp/app.py:41-53`, `frontend/nginx/default.conf.template` | три монтирования |
| Троттлинг | `app/telegram/miniapp/throttle.py`, `resume.py:69` | **в памяти процесса**, а не в общем хранилище |

## Что разведка отметила как недостроенное

`frontend/apps/dashboard/src/pages/dashboard/ui/VacanciesSection.tsx:3` —
статичная заглушка: у дашборда **нет источника данных о вакансиях**.
`handleStatisticsClick` в `App.tsx:20` — пустая функция.

## Границы охвата второй фазы

Схемы строятся для восьми фич, где возможна унификация: F1, F2, F3, F5, F6,
F7, F8, F9. Четыре оставшиеся (F4, F10, F11, F12) малы, изолированы и в
поиске дублирования не участвуют — они описаны здесь и этого достаточно.
