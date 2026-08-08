import psutil  # type: ignore[import-untyped]
from prometheus_client import Counter, Gauge

VACANCIES_COLLECTED_TOTAL = Counter(
    "job_monitor_vacancies_collected_total",
    "Total number of successfully collected vacancies since process start.",
)

MESSAGES_NOT_VACANCY_TOTAL = Counter(
    "job_monitor_messages_not_vacancy_total",
    "Total number of messages classified as not-a-vacancy by LLM.",
)

LLM_ERRORS_TOTAL = Counter(
    "job_monitor_llm_errors_total",
    "Total number of failed LLM calls, labeled by operation and error reason.",
    ["operation", "reason"],
)

SKILL_MATCHES_TOTAL = Counter(
    "job_monitor_skill_matches_total",
    "Total number of accepted user-skill matches across vacancies.",
    ["skill"],
)

USERS_REGISTERED_TOTAL = Counter(
    "job_monitor_users_registered_total",
    "Total number of newly registered users since process start.",
)

USERS_TOTAL = Gauge(
    "job_monitor_users_total",
    "Current total number of users in the database.",
)

ACTIVE_USERS_TOTAL = Gauge(
    "job_monitor_active_users_total",
    "Current number of active users in the database.",
)

# --- Ниже gauge, а не Counter, намеренно ---------------------------------
# Значение восстанавливается из БД при каждом цикле синхронизации, поэтому
# перезапуск процесса его не обнуляет. Counter так не умеет: он живёт
# только в памяти.

DISPATCHED_BY_SPECIALIZATION = Gauge(
    "job_monitor_dispatched_by_specialization",
    "Total dispatched vacancies grouped by specialization.",
    ["specialization"],
)

# Навыки считаются из matched_skills, который заполняется с v0.9.0 —
# у отправок до неё он пустой. Живой счётчик skill_matches_total рядом
# остаётся: он про темп, а этот про накопленное.
DISPATCHED_BY_SKILL = Gauge(
    "job_monitor_dispatched_by_skill",
    "Total dispatched vacancies grouped by matched skill.",
    ["skill"],
)

MESSAGES_SKIPPED = Gauge(
    "job_monitor_messages_skipped",
    "Total scraped messages that did not become vacancies, by reason.",
    ["reason"],
)

FEATURE_USED = Gauge(
    "job_monitor_feature_used",
    "Total feature interactions, by feature.",
    ["feature"],
)

MATCH_REJECTED = Gauge(
    "job_monitor_match_rejected",
    "Total vacancies rejected for a user by a profile filter, by reason.",
    ["reason"],
)

USERS_WITH_PROFILE = Gauge(
    "job_monitor_users_with_profile",
    "Current number of users who filled specializations and skills.",
)

USERS_WITHOUT_DISPATCH = Gauge(
    "job_monitor_users_without_dispatch",
    "Current number of users who never received a single vacancy.",
)

AVG_SKILLS_PER_PROFILE = Gauge(
    "job_monitor_avg_skills_per_profile",
    "Average number of skills across filled profiles.",
)

VACANCIES_DISPATCHED = Gauge(
    "job_monitor_vacancies_dispatched",
    "Total vacancies delivered to users.",
)

VACANCY_FEEDBACK = Gauge(
    "job_monitor_vacancy_feedback",
    "Total feedback marks left on delivered vacancies, by verdict.",
    ["verdict"],
)


PROCESS_RSS_BYTES = Gauge(
    "job_monitor_process_rss_bytes",
    "Resident set size (RSS) memory used by the current process in bytes.",
)

_PROCESS = psutil.Process()


def _current_process_rss_bytes() -> float:
    try:
        return float(_PROCESS.memory_info().rss)
    except Exception:
        return 0.0


PROCESS_RSS_BYTES.set_function(_current_process_rss_bytes)
