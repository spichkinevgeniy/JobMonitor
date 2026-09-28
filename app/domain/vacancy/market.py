"""Агрегаты по всем вакансиям для публичной страницы рынка.

Это сырые счётчики из базы. Что из них показывать и какие выборки
слишком малы, решает прикладной сервис.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SalarySample:
    """Медиана зарплаты и число вакансий, по которым она посчитана."""

    median: int | None
    sample: int


@dataclass(frozen=True, slots=True)
class MarketAggregates:
    # Окно счётчиков: вакансии, направления, форматы, навыки.
    vacancies: int
    with_salary: int
    channels: int
    by_specialization: dict[str, int]
    by_work_format: dict[str, int]
    by_skill: dict[str, int]
    # Окно зарплат длиннее: иначе по небольшим направлениям медиан нет.
    salary_by_specialization: dict[str, SalarySample]
    salary_by_specialization_grade: dict[tuple[str, str], SalarySample]
    # За всё время.
    all_time: int
