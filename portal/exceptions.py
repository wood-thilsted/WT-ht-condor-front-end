class AppError(Exception):
    pass


class ConfigurationError(AppError):
    pass


class CondorToolException(Exception):
    pass
