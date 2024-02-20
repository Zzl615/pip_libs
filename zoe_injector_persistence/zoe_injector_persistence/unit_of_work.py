import abc


class AsyncUnitOfWork(abc.ABC):
    @abc.abstractmethod
    async def __aenter__(self):
        pass

    @abc.abstractmethod
    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    @abc.abstractmethod
    async def commit(self) -> None:
        pass

    @abc.abstractmethod
    async def rollback(self) -> None:
        pass
