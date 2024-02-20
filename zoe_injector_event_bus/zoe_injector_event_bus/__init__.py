from typing import List, Tuple

import injector
from aio_pika import connect_robust
from async_injection_provider import async_provider
from contextvar_request_scope import ContextVarRequestScope
from eventware import OutBox, EventPoster, OutBoxEventPoster, EventReceiver, AioPikaEventReceiver, \
    InjectorBasedAsyncEventBus, EventBus, EventHandlerClass, EventHandler
from sqlalchemy.ext.asyncio import AsyncSession

from zoe_injector_event_bus.out_box import SQLAlchemyOutBox
from zoe_injector_event_bus.rabbitmq_connection_manager import RabbitMQConnectionManager


class EventPosterModule(injector.Module):
    @injector.provider
    def outbox(self, session: AsyncSession) -> OutBox:
        return SQLAlchemyOutBox(session)

    @injector.provider
    def event_poster(self, outbox: OutBox) -> EventPoster:
        return OutBoxEventPoster(outbox)


class EventBusModule(injector.Module):

    def __init__(
            self,
            rabbitmq_uri,
            queue_names,
            subscribes: List[Tuple[str, EventHandler]],
            prefetch_count=10,
    ) -> None:
        self.rabbitmq_uri = rabbitmq_uri
        self.queue_names = queue_names
        self.prefetch_count = int(prefetch_count)
        self.subscribes = subscribes

    @injector.singleton
    @injector.provider
    def robust_connection(self) -> RabbitMQConnectionManager:
        return RabbitMQConnectionManager()

    @injector.provider
    def event_receiver(
            self,
            the_injector: injector.Injector,
            rabbitmq_connection_manager: RabbitMQConnectionManager,
    ) -> EventReceiver:
        return AioPikaEventReceiver(
            self.queue_names,
            rabbitmq_connection_manager.connection,
            the_injector,
            self.prefetch_count,
            scope_class=ContextVarRequestScope,
        )

    @injector.provider
    @async_provider
    async def event_bus(self, receiver: EventReceiver, the_injector: injector.Injector) -> EventBus:
        event_bus = InjectorBasedAsyncEventBus(None, receiver, the_injector)
        # 在这里绑定事件与事件处理类
        for subscribe in self.subscribes:
            await event_bus.subscribe(subscribe[0], subscribe[1])
        return event_bus
