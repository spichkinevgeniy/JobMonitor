from datetime import date

from app.application.services.weekly_pulse_service import MIN_WEEKLY_MATCHES, WeeklyPulse
from app.domain.matching.entities import MatchRejectionReason

_MONTHS_GENITIVE = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)

_FILTER_LABELS = {
    MatchRejectionReason.SALARY: "по зарплате",
    MatchRejectionReason.FORMAT: "по формату работы",
    MatchRejectionReason.GRADE: "по грейду",
    MatchRejectionReason.EXPERIENCE: "по опыту",
}


def _plural(count: int, one: str, few: str, many: str) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return one
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return few
    return many


def _format_day(day: date) -> str:
    return f"{day.day} {_MONTHS_GENITIVE[day.month - 1]}"


def format_week_range(start: date, last: date) -> str:
    """«21–27 сентября», а на стыке месяцев — «29 сентября – 5 октября»."""
    if start.month == last.month:
        return f"{start.day}–{_format_day(last)}"
    return f"{_format_day(start)} – {_format_day(last)}"


def _format_change(current: int, previous: int) -> str:
    if previous == 0:
        return ""
    change = round((current - previous) * 100 / previous)
    if change == 0:
        return " (как на прошлой неделе)"
    return f" ({change:+d}% к прошлой неделе)"


def _format_amount(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def build_weekly_pulse_text(pulse: WeeklyPulse) -> str:
    week = format_week_range(pulse.week.start_date, pulse.week.last_date)
    lines = [
        f"📊 Ваш рынок за неделю {week}",
        "",
        f"Подходящих вакансий: {pulse.matched}"
        f"{_format_change(pulse.matched, pulse.matched_previous)}",
    ]
    if pulse.sent:
        sent_line = f"Отправили вам: {pulse.sent}"
        if pulse.rejected:
            sent_line += f", из них «не подходит»: {pulse.rejected}"
        lines.append(sent_line)

    details: list[str] = []
    if pulse.salary is not None:
        profile = pulse.salary.specialization
        if pulse.salary.grade is not None:
            profile += f" · {pulse.salary.grade.value.title()}"
        sample = pulse.salary.sample
        details.append(
            f"💰 Медиана зарплаты {profile} за 4 недели: {_format_amount(pulse.salary.amount)} ₽ "
            f"(по {sample} {_plural(sample, 'вакансии', 'вакансиям', 'вакансиям')} с зарплатой)"
        )
    if pulse.top_rejection is not None:
        count = pulse.top_rejection.count
        label = _FILTER_LABELS.get(pulse.top_rejection.reason, pulse.top_rejection.reason.value)
        details.append(
            f"🧹 Больше всего отсеял фильтр {label}: {count} "
            f"{_plural(count, 'вакансия', 'вакансии', 'вакансий')}"
        )

    if details:
        lines.append("")
        lines.extend(details)
    return "\n".join(lines)


def build_pulse_preview_note(pulse: WeeklyPulse) -> str:
    """Для /pulse_preview: видно, ушла бы такая сводка человеку или нет."""
    if pulse.worth_sending:
        return "Предпросмотр: такую сводку бот отправил бы в понедельник."
    return (
        f"Предпросмотр: такую сводку бот не отправил бы — подходящих вакансий "
        f"{pulse.matched}, а нужно не меньше {MIN_WEEKLY_MATCHES}."
    )


def build_pulse_unsubscribed_text() -> str:
    return "Сводку больше не пришлём. Включить её снова можно в /settings."


def build_pulse_toggle_label(enabled: bool) -> str:
    return f"📊 Сводка по понедельникам: {'вкл' if enabled else 'выкл'}"
