import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import List
from eventware import Event
from zoe_injector_event_bus.snowflake import IdWorker

id_worker = IdWorker(1, 1, 0)

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent(Event):
    event_id: str = field(init=False)
    timestamp: datetime = field(init=False)
    command_id: str = field(init=False)

    def __post_init__(self):
        self.event_id = id_worker.get_id()
        self.timestamp = datetime.now()
        self.command_id = None


class EventMixin:

    def __init__(self) -> None:
        self._pending_domain_events: List[DomainEvent] = []

    def _record_event(self, event: DomainEvent) -> None:
        logger.info(f"event sent: {event}")
        self._pending_domain_events.append(event)

    @property
    def domain_events(self) -> List[DomainEvent]:
        return self._pending_domain_events[:]

    def clear_events(self) -> None:
        self._pending_domain_events.clear()
