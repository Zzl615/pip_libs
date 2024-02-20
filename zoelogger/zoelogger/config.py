import datetime
from typing import Optional, Callable, List, Union

import attr

__all__ = [
    "ZoeLoggingConfig",
    "LoggingToLogstash",
    "LoggingToFile",
    "LoggingCommonConfig",
    "LoggingToFilebeat",
]


@attr.dataclass
class LoggingToLogstash:
    host: str = attr.ib()
    port: int = attr.ib()
    index_name: str = attr.ib()
    async_sender: bool = attr.ib(default=True)
    async_concurrency: int = attr.ib(default=1)
    enqueue: bool = attr.ib(default=False)
    diagnose: bool = attr.ib(default=True)


@attr.dataclass
class LoggingToFile:
    path: str
    rotation: Optional[Union[str, datetime.time]] = attr.ib(default=None)
    enqueue: bool = attr.ib(default=False)
    diagnose: bool = attr.ib(default=True)


@attr.dataclass
class LoggingCommonConfig:
    span_id_getter: Optional[Callable[[], str]] = attr.ib(default=None)
    trace_id_getter: Optional[Callable[[], str]] = attr.ib(default=None)
    instance_descriptor_getter: Optional[Callable[[], str]] = attr.ib(default=None)
    override_logger_names: Optional[List[str]] = attr.ib(default=None)
    level_map: Optional[dict] = attr.ib(default=None)


@attr.dataclass
class LoggingToFilebeat:
    index_name: str = attr.ib()
    enqueue: bool = attr.ib(default=False)
    diagnose: bool = attr.ib(default=True)
    path: str = attr.ib(default="/logs/app.log")  # 约定


@attr.dataclass
class ZoeLoggingConfig:
    app_name: str = attr.ib()
    log_level: str = attr.ib(default="INFO")

    common_config: LoggingCommonConfig = attr.ib(default=LoggingCommonConfig())

    logstash: LoggingToLogstash = attr.ib(default=None)
    file: LoggingToFile = attr.ib(default=None)
    filebeat: LoggingToFilebeat = attr.ib(default=None)
