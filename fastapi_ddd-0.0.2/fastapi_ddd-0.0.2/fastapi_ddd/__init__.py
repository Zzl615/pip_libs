import logging
import uuid
from typing import TypeVar, Generic, Optional

from fastapi.routing import APIRoute
from pydantic.generics import GenericModel

from fastapi_ddd.foundation.request_scope import AsyncRequestScope
from fastapi_ddd.foundation.request_context import RequestId

logger = logging.getLogger(__name__)

__all__ = ["InjectorAPIRoute", "CommonResp", "RequestId"]


class InjectorAPIRoute(APIRoute):

    async def handle(self, scope, receive, send) -> None:
        try:
            injector = scope['app'].state.injector
        except:
            raise RuntimeError('Injector not found')
        try:
            async_request_scope = injector.get(AsyncRequestScope)
        except Exception:
            logger.exception("AsyncRequestScope not found")
            raise RuntimeError('InjectorAPIRoute: AsyncRequestScope not found. injector: {}'.format(id(injector)))
        try:
            request_id = injector.get(RequestId)
        except Exception:
            logger.exception("RequestId not found")
            raise RuntimeError('InjectorAPIRoute: RequestId not found. injector: {}'.format(id(injector)))
        with async_request_scope:
            request_id.set(uuid.uuid4().hex)
            return await super().handle(scope, receive, send)


DataT = TypeVar('DataT')


class CommonResp(GenericModel, Generic[DataT]):
    status: int = 0
    message: str = 'ok'
    result: Optional[DataT] = None
