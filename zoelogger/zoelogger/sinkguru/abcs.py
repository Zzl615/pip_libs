import abc
from zoelogger.sinkguru import Message


class LogFormatter(abc.ABC):
    @abc.abstractmethod
    def format(self, message: Message) -> bytes:
        pass


class LogSender(abc.ABC):
    @abc.abstractmethod
    async def send(self, message: bytes) -> None:
        pass


class LogBuffer(abc.ABC):
    @abc.abstractmethod
    async def read(self) -> bytes:
        pass

    @abc.abstractmethod
    async def write(self, data: bytes) -> None:
        pass

    @abc.abstractmethod
    def __len__(self) -> int:
        pass
