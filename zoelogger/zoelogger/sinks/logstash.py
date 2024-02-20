import abc
import json
import asyncio
import logging
import socket
from logging.handlers import SocketHandler

from dateutil import tz
from datetime import timezone
from typing import Union, List, Type, cast, Dict, Tuple, Optional

from zoelogger.config import LoggingToLogstash, ZoeLoggingConfig
from zoelogger.level import default_level_map
from zoelogger.sinkguru import LogFormatter, Message, LogBuffer, LogSender
from zoelogger.sinkguru.impl import LocalBytesBuffer, LogStashTcpSender
from zoelogger.sinks.common import elk_format


class LogStashLogFormatter(LogFormatter):
    def __init__(
        self,
        app_name: str,
        log_index_name: str,
        level_map: Optional[Dict[int, Tuple[int, str]]],
    ) -> None:
        self._app_name = app_name
        self._log_index_name = log_index_name.lower()
        self._timezone = tz.gettz("Asia/Shanghai")
        self._level_map = level_map or default_level_map

    def format(self, message: Message) -> bytes:
        json_record = elk_format(
            message, self._level_map, self._app_name, self._log_index_name
        )
        # print(json.dumps(json_record))
        # https://docs.graylog.org/docs/gelf
        # At the current time, GELF TCP only supports uncompressed and non-chunked payloads.
        # Each message needs to be delimited with a null byte (\0) when sent in the same TCP connection.
        return json.dumps(json_record).encode() + b"\0"


class AsyncLogStashSink:
    def __init__(
        self,
        host: str,
        port: int,
        formatter: LogFormatter,
        sender_class: Type[LogStashTcpSender] = LogStashTcpSender,
        buffer_class: Type[LogBuffer] = LocalBytesBuffer,
        concurrency: int = 1,
    ) -> None:
        self._host = host
        self._port = port
        self._formatter = formatter
        self._concurrency = concurrency
        self._buffer_class = buffer_class
        self._sender_class = sender_class
        self._buffer: Union[LogBuffer, None] = None
        self._senders: List[LogSender] = []

    def _initialize(self) -> None:
        self._buffer = self._buffer_class()
        for i in range(self._concurrency):
            sender = self._sender_class(
                host=self._host,
                port=self._port,
                buffer=self._buffer,
            )
            self._senders.append(sender)
            asyncio.create_task(sender())

    async def __call__(self, message):
        if self._buffer is None:
            self._initialize()
        formatted = self._formatter.format(message)
        assert self._buffer is not None
        await self._buffer.write(formatted)


class SyncLogStashSink:
    def __init__(self, host: str, port: int, formatter: LogFormatter) -> None:
        self._host = host
        self._port = port
        self._formatter = formatter
        self.sender = SocketHandler(host, port).send

    def __call__(self, message):
        formatted = self._formatter.format(message)
        self.sender(formatted)


def check_tcp(host: str, port: int) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        s.send(b"PING")
        print(f"tcp connect: {host}:{port}")  # 打到标准输出，方便在k8s中查看
        # logging.info(f"tcp connect: {host}:{port}")
        s.close()
        return True
    except Exception as e:
        print(f"tcp connect error: {host}:{port}")


def _config_to_sink_logstash(config: ZoeLoggingConfig):
    if not config.logstash:
        return None

    check_tcp(config.logstash.host, config.logstash.port)

    json_formatter = LogStashLogFormatter(
        app_name=config.app_name,
        log_index_name=config.logstash.index_name,
        level_map=config.common_config.level_map,
    )
    if config.logstash.async_sender:
        sinker = AsyncLogStashSink(
            host=config.logstash.host,
            port=config.logstash.port,
            formatter=json_formatter,
            concurrency=config.logstash.async_concurrency,
        )
    else:
        sinker = SyncLogStashSink(
            host=config.logstash.host,
            port=config.logstash.port,
            formatter=json_formatter,
        )

    return sinker
