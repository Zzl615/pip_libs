import abc
from typing import Any
from contextvars import ContextVar

_request_id = ContextVar("request_id")
_request_user_id = ContextVar("request_user_id")
_request_app_id = ContextVar("request_app_id")


class AbstractRequestContext(abc.ABC):

    def __init__(self, request_context_var: ContextVar):
        self._request_context_var = request_context_var

    def get(self, value: Any = None) -> Any:
        try:
            return self._request_context_var.get()
        except LookupError:
            if value is None:
                return
            self.set(value)
            return self._request_context_var.get()

    def set(self, value: Any) -> None:
        self._request_context_var.set(value)

    def __str__(self):
        value = self.get()
        if value is None:
            return str(self._request_context_var)
        return str(value)


class RequestId(AbstractRequestContext):
    def __init__(self):
        super().__init__(_request_id)


class RequestUserId(AbstractRequestContext):
    def __init__(self):
        super().__init__(_request_user_id)


class RequestAppId(AbstractRequestContext):
    def __init__(self):
        super().__init__(_request_app_id)
