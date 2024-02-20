import json

import sqlalchemy
from eventware.abc import OutBox, EventBus, Event
from sqlalchemy import event as sqlalchemy_event, MetaData
from sqlalchemy.ext.asyncio import AsyncSession

from zoe_injector_event_bus.event import EventMixin, DomainEvent

metadata = MetaData()


@sqlalchemy_event.listens_for(EventMixin, "load", propagate=True)
def receive_load_event(event_mixin, _):
    event_mixin._pending_domain_events = []


event_table = sqlalchemy.Table(
    'event',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.BigInteger, primary_key=True),
    sqlalchemy.Column('name', sqlalchemy.String(length=64), nullable=False),
    sqlalchemy.Column('detail', sqlalchemy.Text, nullable=False),
    sqlalchemy.Column('created_at', sqlalchemy.DateTime, nullable=False),
)


async def _add_event(session, event: DomainEvent):
    detail = {k: getattr(event, k) for k in event.__annotations__.keys()}
    detail_json = json.dumps(detail)
    await session.execute(event_table.insert().values(id=event.event_id,
                                                      name=event.__class__.__name__,
                                                      detail=detail_json,
                                                      created_at=event.timestamp))


class SQLAlchemyOutBox(OutBox):
    """
    事件只是add 进了session，随整个请求的事务一起commit
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session

    async def add(self, event: Event) -> None:
        await _add_event(self._session, event)
