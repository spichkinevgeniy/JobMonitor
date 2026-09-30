from app.domain.shared.domain_errors import DomainError


class VacancyDomainError(DomainError):
    pass


class ValidationError(VacancyDomainError):
    pass


class DuplicateVacancyError(VacancyDomainError):
    """Вакансия с таким же текстом уже сохранена.

    Обычно дубль отсекается заранее, по хэшу текста. Сюда доходит гонка:
    два одинаковых сообщения проверены одновременно, и второе упирается в
    уникальность при сохранении.
    """
