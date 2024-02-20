from typing import Optional, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from zoe_fastapi_exception.error_codes import ErrorCode, SERVICE_ERROR, REQUEST_ERROR

__all__ = [
    'ErrorResponse',
    'ZoeException',
    'ZoeFastAPIExceptionManager',
]

class ErrorResponse(BaseModel):
    code: int = Field(
            ..., description="human-readable 服务应该有相对较少的（大约20个）code值, 客户端能对这些类型的问题做出处理"
        )
    message: str = Field(..., description="终端用户查看消息")
    error: Optional[str] = Field("", description="错误信息")
    # status: int = Field(..., description="和response status code相同")
    

    @staticmethod
    def build(
            status_code: int,
            message: str,
            code: ErrorCode,
            message_to_developer: str,
            target: str = None,
            additional_info: Dict = None,
    ) -> JSONResponse:
        return JSONResponse(
            content=ErrorResponse(
                message=message,
                # status=status_code,
                code=code,
                error=message_to_developer,
            ).dict(),
            status_code=status_code,
        )

exceptions = set()  # 用于存储所有的异常类，用于统计异常会导致 接口返回哪些 response status code，用于生成 OpenAPI 文档


class ZoeExceptionMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = type.__new__(cls, name, bases, attrs)
        exceptions.add(new_class)
        return new_class


class ZoeException(Exception, metaclass=ZoeExceptionMeta):
    """
    通用异常，自定义的异常应该继承自这个类
    当在一次请求中抛出异常时，会自动调用这个类的response方法 返回一个JSONResponse

    code: ErrorCode 异常代码 human-readable 服务应该有相对较少的（大约20个）code值, 客户端能对这些类型的问题做出处理
    is_safe_exception: bool 是否是安全异常，如果是，则不会记录日志
    response_status: int 和response status code相同
    """
    code: ErrorCode = SERVICE_ERROR
    is_safe_exception = False
    response_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(
            self,
            message: str,
            message_to_developer: str = None,
            target: str = None,
            additional_info: Dict = None,
    ):
        """
        :param message: 为终端用户提供的消息
        :param message_to_developer: 不是给客户展示的 是给开发人员看的
        :param target: 特定错误的目标（例如，出错属性的名称）
        :param additional_info: 额外的信息 多一些信息方便debug
        """
        self.message = message
        self.message_to_developer = message_to_developer
        self.target = target
        self.additional_info = additional_info

    async def response(self) -> JSONResponse:
        return ErrorResponse.build(
            message=self.message,
            status_code=self.response_status,
            code=self.code,
            message_to_developer=self.message_to_developer or '',
            target=self.target,
            additional_info=self.additional_info,
        )


class UnauthorizedException(ZoeException):
    code = SERVICE_ERROR
    is_safe_exception = True
    response_status = status.HTTP_401_UNAUTHORIZED


class ZoeFastAPIExceptionManager:

    def __init__(self, debug: bool = False):
        self.debug = debug

    async def handle(self, exc):
        if isinstance(exc, RequestValidationError):  # 其他第三包提供的异常 参数验证异常处理
            return ErrorResponse.build(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="参数错误",
                code=REQUEST_ERROR,
                message_to_developer=str(exc),
            )

        if isinstance(exc, ZoeException):
            return await exc.response()

        return ErrorResponse.build(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="系统异常",
            code=SERVICE_ERROR,
            message_to_developer='报错了 查日志吧' if not self.debug else str(exc),
        )

    @classmethod
    def router_responses_addon(cls) -> dict:
        exceptions_response_code = {
            exception.response_status
            for exception in exceptions
            if hasattr(exception, 'response_status')
        }
        return {str(s): {"model": ErrorResponse} for s in exceptions_response_code}

    def setup(self, app: FastAPI) -> None:

        async def exception_handler(
                request: Request,
                exc: Exception,
        ) -> JSONResponse:
            return await self.handle(exc)

        app.add_exception_handler(RequestValidationError, exception_handler)
        app.add_exception_handler(Exception, exception_handler)

        async def middleware(
                request: Request,
                call_next,
        ) -> JSONResponse:
            try:
                response = await call_next(request)
                return response
            except ZoeException as exc:
                if exc.is_safe_exception:
                    # print('got safe exception:', exc)
                    return await self.handle(exc)
                else:
                    raise exc

        app.add_middleware(BaseHTTPMiddleware, dispatch=middleware)
