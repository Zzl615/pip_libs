from typing import Any, TypeVar

from fastapi import Depends, Request
from starlette.websockets import WebSocket

from fastapi_injector.attach import get_injector_instance

BoundInterface = TypeVar("BoundInterface", bound=type)


def Injected(interface: BoundInterface) -> Any:  # pylint: disable=invalid-name
    """
    Asks your injector instance for the specified type,
    allowing you to use it in the route.
    """

    def inject_into_route(request: Request = None, websocket: WebSocket = None) -> BoundInterface:
        if not request and not websocket:
            raise RuntimeError("Injected() must be used in a route")
        app = request.app if request else websocket.app
        return get_injector_instance(app).get(interface)

    return Depends(inject_into_route)
