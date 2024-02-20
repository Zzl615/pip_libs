import logging

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_ddd.foundation.unit_of_work import AsyncUnitOfWork

logger = logging.getLogger(__name__)


class AsyncSqlAlchemyUnitOfWork(AsyncUnitOfWork):
    def __init__(
            self,
            session: AsyncSession,
    ) -> None:
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self):
        try:
            await self.session.commit()
        except Exception as ex:
            if 'Duplicate entry' in str(ex):
                logger.error(f'Duplicate entry: {ex}')
            else:
                logger.exception(f"session commit error: {ex}")
            # 不许rollback 保证一次请求只能有一个事务，不能多次commit
            # 如果允许多次commit，那请求进行中时，一旦出现服务终止，会导致数据不一致。
            # await self.rollback()
            raise

    async def rollback(self):
        await self.session.rollback()
