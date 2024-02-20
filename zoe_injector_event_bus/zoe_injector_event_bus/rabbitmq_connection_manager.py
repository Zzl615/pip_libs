import dataclasses

from aio_pika import RobustConnection


@dataclasses.dataclass
class RabbitMQConnectionManager:
    connection: RobustConnection = None
