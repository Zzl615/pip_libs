from typing import Callable

import aioredis


class AlreadyLocked(Exception):
    pass


class Lock:
    """
    redis 锁
    :param redis
    :param name
    :raise AlreadyLocked
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        name: str,
        timeout: int,
        lock_name_prefix,
        lock_value,
    ) -> None:
        self.lock_name_prefix = lock_name_prefix
        self.lock_value = lock_value
        self._redis = redis
        self._lock_name = self.lock_name_prefix + name
        self._timeout = timeout

    async def __aenter__(self) -> None:
        if not await self._redis.set(
            name=self._lock_name,
            value=self.lock_value,
            ex=self._timeout,
            nx=True,
        ):
            raise AlreadyLocked

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type != AlreadyLocked:
            await self._redis.delete(self._lock_name)
        return False


LockFactory = Callable[[str, int], Lock]


def get_mock_lock_factory() -> LockFactory:
    class MockLock(Lock):
        def __init__(self):
            pass

        async def __aenter__(self):
            pass

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    def mock_lock_factory(name, timeout):
        return MockLock()

    return mock_lock_factory
