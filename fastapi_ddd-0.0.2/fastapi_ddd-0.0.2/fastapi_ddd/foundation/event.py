import logging
import datetime
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from fastapi_ddd.foundation.deps.snowflake import IdWorker

data_center_id = os.getenv('SNOWFLAKE_DATA_CENTER_ID', 1)
work_id = os.getenv('SNOWFLAKE_WORKER_ID', 1)
sequence = os.getenv('SNOWFLAKE_SEQUENCE', 0)

id_worker = IdWorker(data_center_id, work_id, sequence)

logger = logging.getLogger(__name__)


@dataclass
class Event:
    event_id: str = field(init=False)
    timestamp: datetime = field(init=False)
    command_id: str = field(init=False)

    def __post_init__(self):
        self.event_id = id_worker.get_id()
        self.timestamp = datetime.now()
        self.command_id = None


class EventMixin:
    def __init__(self) -> None:
        self._pending_domain_events: List[Event] = []

    def _record_event(self, event: Event) -> None:
        logger.info(f"event sent: {event}")
        self._pending_domain_events.append(event)

    @property
    def domain_events(self) -> List[Event]:
        return self._pending_domain_events[:]

    def clear_events(self) -> None:
        self._pending_domain_events.clear()
