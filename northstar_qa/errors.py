class AppError(Exception):
    """An expected error that can be shown directly to a CLI user."""


class DocumentLoadError(AppError):
    pass


class IndexError(AppError):
    pass


class QuestionError(AppError):
    pass
