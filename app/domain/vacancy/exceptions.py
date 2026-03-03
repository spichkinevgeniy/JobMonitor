from app.domain.shared.domain_errors import DomainError


class VacancyDomainError(DomainError):
    pass


class NotAVacancyError(VacancyDomainError):
    pass


class ValidationError(VacancyDomainError):
    pass
