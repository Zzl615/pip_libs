import injector
from async_request_scope import AsyncRequestScope

request_scope = injector.ScopeDecorator(AsyncRequestScope)
