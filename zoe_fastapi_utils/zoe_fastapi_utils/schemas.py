import dataclasses
from typing import Any, Generic, List, Optional, TypeVar

import pydantic
from fastapi.responses import JSONResponse
from pydantic.generics import GenericModel

T = TypeVar("T")


class CommonResp(GenericModel, Generic[T]):
    message: str = "ok"
    result: Optional[T] = None

    @classmethod
    def success(cls, data: T, status_code: int = 200) -> JSONResponse:
        if not isinstance(data, dict):
            if isinstance(data, pydantic.BaseModel):
                data = data.dict()
            elif dataclasses.is_dataclass(data):
                data = dataclasses.asdict(data)
            else:
                pass
        return JSONResponse(
            content={"message": "ok", "result": data}, status_code=status_code
        )

    @classmethod
    def fail(cls, message: str, status_code: int) -> JSONResponse:
        return JSONResponse(content={"message": message}, status_code=status_code)


class CommonListResp(GenericModel, Generic[T]):
    class ListDto(GenericModel, Generic[T]):
        total: int
        items: List[T]

    result: ListDto[T]
    message: str = "ok"

    @classmethod
    def from_list(cls, items: List[T], total: int) -> "CommonListResp[T]":
        return cls(result=cls.ListDto[T](total=total, items=items))

    @classmethod
    def from_single(cls, item: T, total: int) -> "CommonListResp[T]":
        return cls.from_list([item], total)

    @classmethod
    def empty(cls, total: int = 0) -> "CommonListResp[T]":
        return cls.from_list([], total)

    @classmethod
    def fail(cls, message: str, status_code) -> JSONResponse:
        return JSONResponse(content={"message": message}, status_code=status_code)
