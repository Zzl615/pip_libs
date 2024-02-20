import logging

import aioredis
import injector
from async_injection_provider import async_provider
from contextvar_request_scope import request_scope
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from zoe_injector_persistence.lock_factory import Lock, LockFactory
from zoe_injector_persistence.unit_of_work import AsyncUnitOfWork
from zoe_injector_persistence.unit_of_work_impl import AsyncSqlAlchemyUnitOfWork

_logger = logging.getLogger("zoe_injector_persistence")

__all__ = [
    "RedisModule",
    "DatabaseModule",
    "LockFactory",
    "AsyncUnitOfWork",
]


class RedisModule(injector.Module):
    """
    redis 模块
    - ✅ 支持 asyncio (通过 aioredis)
    - ❌ 不支持配置 hot-reload

    提供对象：
        - Redis:
            from aioredis import Redis
        - LockFactory: Redis锁工厂函数
            from zoe_injector_persistence.lock_factory import LockFactory
    """

    def __init__(
        self,
        dsn: str,
        lock_name_prefix: str = "lock:",
        lock_timeout: int = 30,
        lock_value: bytes = b"1",
    ):
        self.redis_dsn = dsn
        self.lock_name_prefix = lock_name_prefix
        self.lock_timeout = lock_timeout
        self.lock_value = lock_value

    @injector.singleton
    @injector.provider
    def lock_factory(self, redis: aioredis.Redis) -> LockFactory:
        def factory(name: str, timeout: int = self.lock_timeout) -> Lock:
            return Lock(
                redis,
                name,
                timeout,
                lock_name_prefix=self.lock_name_prefix,
                lock_value=self.lock_value,
            )

        return factory

    @injector.singleton
    @async_provider
    async def provide_async_redis_pool(self) -> aioredis.Redis:
        return await aioredis.from_url(self.redis_dsn)


class DatabaseModule(injector.Module):
    """
    sqlalchemy 数据库模块
    - ✅ 支持 asyncio (通过 aiomysql)
    - ✅ 支持 request scope
    - ❌ 不支持配置 hot-reload

    提供对象：
        - AsyncSession:
            from sqlalchemy.ext.asyncio import AsyncSession
        - AsyncUnitOfWork:
            from zoe_injector_persistence.unit_of_work import AsyncUnitOfWork

    :param dsn: `mysql+aiomysql://<user>:<password>@<ip>:<port>/<database>`
    :param pool_size: 数据库连接池大小
    """

    def __init__(
        self,
        dsn: str,
        pool_size: int = 5,
        pool_max_overflow: int = 50,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        debug: bool = False,
    ):
        self.database_dsn = dsn
        self.database_pool_size = pool_size
        self.database_pool_max_overflow = pool_max_overflow
        self.database_pool_recycle = pool_recycle
        self.database_pool_pre_ping = pool_pre_ping
        self.debug = debug

    @injector.singleton
    @injector.provider
    def mysql_pool(self) -> AsyncEngine:
        engine = create_async_engine(
            self.database_dsn,
            pool_size=self.database_pool_size,
            max_overflow=self.database_pool_max_overflow,
            pool_recycle=self.database_pool_recycle,
            pool_pre_ping=self.database_pool_pre_ping,
            echo=self.debug,
        )
        _logger.debug(f"MySQL pool created: {engine}")
        return engine

    @request_scope
    @injector.provider
    def get_async_session(self, engine: AsyncEngine) -> AsyncSession:
        session = AsyncSession(bind=engine, expire_on_commit=False)
        return session

    @request_scope
    @injector.provider
    def get_async_uow(self, session: AsyncSession) -> AsyncUnitOfWork:
        return AsyncSqlAlchemyUnitOfWork(session)
