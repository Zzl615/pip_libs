import json

import sqlalchemy
from sqlalchemy import event, MetaData
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_ddd.foundation.event import Event, EventMixin
from fastapi_ddd.foundation.event_bus import EventBus

metadata = MetaData()


@event.listens_for(EventMixin, "load", propagate=True)
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


async def post_event(session, event: Event):
    detail = {k: getattr(event, k) for k in event.__annotations__.keys()}
    detail_json = json.dumps(detail)

    await session.execute(
        event_table.insert().values(
            id=event.event_id,
            name=event.__class__.__name__,
            detail=detail_json,
            created_at=event.timestamp
        )
    )


class MailBoxEventBus(EventBus):

    def __init__(
            self,
            session: AsyncSession,
    ):
        self._session = session

    async def post(self, event: Event) -> None:
        await post_event(self._session, event)
