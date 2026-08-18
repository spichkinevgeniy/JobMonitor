# F1 — Приём вакансий

Вход: `app/telegram/scrapper/handlers.py:43` (`_message_handler`), запуск
слушателя в `:132`. Терминал: строка в `vacancies` и передача в подбор.

## Порядок операций

Зеркалирование идёт **до** разбора, а не после: сначала сообщение
пересылается в mirror-канал (`handlers.py:224`), и только потом считается хеш
и вызывается модель. Это осознанно — рассылка потом делает `copy_message` из
зеркала, а не из исходного канала.

Дедупликация двойная: оптимистичная проверка по `content_hash`
(`vacancy_repository.py:142`) и защита уникальным индексом, чей `IntegrityError`
ловится в `handlers.py:102` с пометкой `source="save"` против `"prefilter"`.
Это настоящая защита от гонки, а не перестраховка.

## Схема

```mermaid
flowchart TD
    S1["TelegramScraper.start<br/>app/telegram/scrapper/handlers.py:132"] --> S4["_resolve_valid_channels<br/>app/telegram/scrapper/handlers.py:145"]
    S4 --> S5{{"TG API get_input_entity<br/>app/telegram/scrapper/handlers.py:150"}}
    S5 -->|ошибка| S6["канал отброшен<br/>app/telegram/scrapper/handlers.py:152"]
    S5 -->|ок| S9["add_event_handler NewMessage<br/>app/telegram/scrapper/handlers.py:138"]
    S9 --> H0["_message_handler<br/>app/telegram/scrapper/handlers.py:43"]
    H0 --> M0["_send_to_mirror<br/>app/telegram/scrapper/handlers.py:200"]
    M0 --> M1{"текст пуст или короче 120<br/>app/telegram/scrapper/handlers.py:204,213"}
    M1 -->|да| SK1["skip TOO_SHORT<br/>app/telegram/scrapper/handlers.py:205,214"]
    M1 -->|нет| M3{{"forward_messages в зеркало<br/>app/telegram/scrapper/handlers.py:224"}}
    M3 -->|ошибка| SK3["skip MIRROR_FAILED<br/>app/telegram/scrapper/handlers.py:231"]
    M3 -->|ок| D1["compute_content_hash sha256<br/>app/domain/vacancy/entities.py:123"]
    D1 --> D3[("SELECT exists_by_content_hash<br/>app/infrastructure/db/repositories/vacancy_repository.py:142")]
    D3 -->|есть| SK4["skip DUPLICATE prefilter<br/>app/telegram/scrapper/handlers.py:70"]
    D3 -->|нет| P0["VacancyService.parse_message<br/>app/application/services/vacancy_service.py:28"]
    P0 --> P2["run_with_llm_retry<br/>app/infrastructure/llm_runtime.py:20"]
    P2 --> P3{{"agent.run OpenRouter<br/>app/infrastructure/extractors/vacancy_extractor.py:14"}}
    P3 -->|429/5xx, 3 попытки| E2["TemporaryLLMUnavailableError<br/>app/infrastructure/llm_runtime.py:43"]
    P3 --> P5{"is_vacancy<br/>app/application/services/vacancy_service.py:46"}
    P5 -->|нет| SK5["skip NOT_VACANCY<br/>app/application/services/vacancy_service.py:53"]
    P5 -->|да| V1["Vacancy.create, валидация<br/>app/domain/vacancy/entities.py:70"]
    V1 -->|нет специализаций или навыков| E3["ValidationError<br/>app/domain/vacancy/entities.py:99"]
    V1 --> V3["upsert<br/>app/infrastructure/db/repositories/vacancy_repository.py:160"]
    V3 --> V6[("COMMIT<br/>app/infrastructure/db/uow/base.py:25")]
    V6 -->|нарушение уникальности| E4["skip DUPLICATE save<br/>app/telegram/scrapper/handlers.py:103"]
    V6 --> X2["передача в подбор<br/>app/application/services/matcher_service.py:31"]
    E3 --> E6["catch-all: skip PARSE_FAILED<br/>app/telegram/scrapper/handlers.py:122"]
```

## Две дыры в наблюдаемости

**`SkipReason.NO_SKILLS` объявлена, но не вызывается нигде** — ноль call sites
во всём `app/`. Вакансия без специализации или навыков падает с
`ValidationError` (`entities.py:99`), ловится общим обработчиком
(`handlers.py:119`) и считается как **`parse_failed`**. То есть потеря видна в
метриках, но под чужим именем, и отделить её от настоящих сбоев разбора нельзя.

**`TemporaryLLMUnavailableError` не увеличивает ни один счётчик пропусков**
(`handlers.py:111-118` только логирует). Недоступность модели видна лишь в
`LLM_ERRORS_TOTAL`, но не в воронке «почему сообщение не стало вакансией».

## Побочные эффекты

Telegram: `get_input_entity` при старте, `forward_messages` на каждое
сообщение. LLM: один вызов на сообщение-кандидат, до трёх попыток с
экспоненциальной паузой (`llm_runtime.py:11,24,58`). База: два SELECT по хешу,
INSERT либо UPDATE, COMMIT.

## Внешние зависимости

Подбор — `matcher_service.py:31`. Общий рантайм LLM — `llm_runtime.py:20`,
тот же, что у разбора резюме (`llm.py:132,221`). Наблюдаемость —
`observability/service.py:23`, счётчики через `counter_store.py:32`.
Конфигурация каналов — `config.py:130`, `channels_map.json`.

## Пробелы разведки

Не проверен уникальный индекс на `content_hash` в моделях и миграциях —
существование выведено из наличия обработчика `IntegrityError`.
Не установлено, при каком условии выбирается `NoOpObservabilityService`
(`service.py:52`) — при нём все счётчики этой фичи молчат.
