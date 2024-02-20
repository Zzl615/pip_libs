import abc
from contextvars import ContextVar
from typing import Any, List, Type

import injector

_request_id = ContextVar("request_id")
_request_user_info = ContextVar("request_user_info")
_request_trace_id = ContextVar("request_trace_id")
_request_span_id = ContextVar("request_span_id")


class AbstractRequestContext(abc.ABC):
    _request_context_var = None

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
    _request_context_var = _request_id


class RequestUserInfo(AbstractRequestContext):
    _request_context_var = _request_user_info


class RequestTraceId(AbstractRequestContext):
    _request_context_var = _request_trace_id


class RequestSpanId(AbstractRequestContext):
    _request_context_var = _request_span_id


class RequestContextModule(injector.Module):
    def __init__(self, request_contexts: List[Type[AbstractRequestContext]]):
        self.request_contexts = request_contexts

    def configure(self, binder: injector.Binder) -> None:
        for request_context in self.request_contexts:
            binder.bind(request_context, request_context(), scope=injector.singleton)
            # print("binding:", binder.get_binding(request_context))
