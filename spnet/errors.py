
class BackendFailure(ValueError):
    pass

class UnexpectedStatus(BackendFailure):
    pass

class TimeoutError(BackendFailure):
    pass


