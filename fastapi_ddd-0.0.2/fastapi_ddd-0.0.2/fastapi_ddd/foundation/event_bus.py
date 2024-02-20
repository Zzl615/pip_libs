import abc

from fastapi_ddd.foundation.event import Event


class EventBus(abc.ABC):

    @abc.abstractmethod
    async def post(self, event: Event) -> None:
        raise NotImplementedError
