class DomainError(Exception):
    """Базовое доменное исключение. Ничего не знает о HTTP."""


class NotFoundError(DomainError):
    """Объект не найден."""


class AlreadyExistsError(DomainError):
    """Объект уже существует."""


class BusinessLogicError(DomainError):
    """Нарушение бизнес-правила."""
