from typing import Optional

import pydantic
from starlette.responses import JSONResponse


class Resp:
    @classmethod
    def success(cls, data: Optional[pydantic.BaseModel] = None, status_code: int = 200) -> JSONResponse:
        if not data:
            return JSONResponse(content={}, status_code=status_code)
        if not issubclass(type(data), pydantic.BaseModel):
            raise ValueError("data must be pydantic.BaseModel")
        return JSONResponse(content=data.dict(by_alias=True), status_code=status_code)

    @classmethod
    def fail(cls, message: str, status_code: int) -> JSONResponse:
        # warning: message is not a dict
        return JSONResponse(content={'message': message, 'status': 1}, status_code=status_code)
