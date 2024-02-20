import logging
import os
import socket
import sys
from types import FrameType
from typing import cast, Callable, Optional, List

from loguru import logger

__all__ = [
    "config_logging",
    "config_logging_optional",
    "reset_logger_level",
    "get_logger_with_custom_level",
]

from loguru._file_sink import FileSink

from zoelogger.config import ZoeLoggingConfig
from zoelogger.level import default_level_map, allowed_levels
from zoelogger.sinks.filebeat import FilebeatLogFormatter, FilebeatFileSink
from zoelogger.sinks.logstash import (
    AsyncLogStashSink,
    SyncLogStashSink,
    LogStashLogFormatter,
    check_tcp,
    _config_to_sink_logstash,
)


class InterceptHandler(logging.Handler):
    """
    logging 转发到 loguru
    """

    def emit(self, record: logging.LogRecord) -> None:
        # print('emit message[', record.getMessage(), ']', logger, id(logger))
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).bind(
            logger_name=record.name
        ).log(
            level,
            record.getMessage(),
            # logger_name=record.name,  # 绝对不要这样加参数 要使用bind
        )
        # 不要在log中加参数
        # 加参数后，loguru 使用 message.format(*args, **kwargs) 来渲染字符串.
        # 当 message 为 json 字符串时, format 函数会抛错
        # 导致问题的代码详见
        # https://github.com/Delgan/loguru/blob/0.6.0/loguru/_logger.py#L1954
        # 如果需要加参数，使用 bind 函数


def _override_logging_loggers(log_level: int, override_logger_names: List[str]):
    # 兼容使用 logging.getLogger(__name__) 的方式
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers = [InterceptHandler(level=log_level)]

    # override_logger_names = ("uvicorn.asgi", "uvicorn.access", "uvicorn.error", 'uvicorn')
    if override_logger_names:
        for logger_name in override_logger_names:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers.clear()
            logging_logger.handlers.append(InterceptHandler(level=log_level))
            logging_logger.propagate = False  # 阻止日志传递给父级handler


def _decode_log_level(level: str) -> int:
    levels = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "warn": logging.WARN,
        "error": logging.ERROR,
    }
    if level:
        _logging_level = levels.get(level.lower(), logging.INFO)
    else:
        _logging_level = logging.INFO
    return _logging_level


def get_logger_with_custom_level(logger_name: str, level: int) -> logging.Logger:
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(level)
    _logger.propagate = False
    _logger.handlers = [InterceptHandler(level=level)]
    return _logger


def reset_logger_level(_logger: logging.Logger, level: int) -> logging.Logger:
    _logger.setLevel(level)
    _logger.propagate = False
    _logger.handlers = [InterceptHandler(level=level)]
    return _logger


def config_logging_optional(config: ZoeLoggingConfig) -> None:
    log_level = _decode_log_level(config.log_level)

    _override_logging_loggers(
        log_level=log_level,
        override_logger_names=config.common_config.override_logger_names,
    )

    def request_filter(record) -> bool:
        span_id = ""
        trace_id = ""
        instance_descriptor = ""
        if config.common_config:
            if config.common_config.span_id_getter:
                span_id = config.common_config.span_id_getter()
            if config.common_config.trace_id_getter:
                trace_id = config.common_config.trace_id_getter()
            if config.common_config.instance_descriptor_getter:
                instance_descriptor = config.common_config.instance_descriptor_getter()
        record.get("extra")["span_id"] = span_id
        record.get("extra")["trace_id"] = trace_id
        record.get("extra")["instance_descriptor"] = instance_descriptor
        return True

    handlers = [
        {
            "sink": sys.stderr,
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {extra[trace_id]} {message}",
            "filter": request_filter,
            # "level": log_level,
        }
    ]
    if config.logstash:
        logstash_sink = _config_to_sink_logstash(config)
        if logstash_sink:
            print("[zoelogger] logstash logging enabled.")
            handlers.append(
                {
                    "sink": logstash_sink,
                    "enqueue": config.logstash.enqueue,
                    # "level": log_level,
                    "filter": request_filter,
                    "diagnose": config.logstash.diagnose,
                }
            )

    if config.file:
        print("[zoelogger] file logging enabled. path: %s" % config.file.path)
        handlers.append(
            {
                "sink": config.file.path,
                # "level": log_level,
                "rotation": config.file.rotation,
                "filter": request_filter,
                "enqueue": config.file.enqueue,
                "diagnose": config.file.diagnose,
            }
        )

    logger.configure(handlers=handlers)

    if config.filebeat:
        log_path = config.filebeat.path
        print("[zoelogger] filebeat logging enabled. path: {}".format(log_path))
        json_formatter = FilebeatLogFormatter(
            app_name=config.app_name,
            log_index_name=config.filebeat.index_name,
            level_map=config.common_config.level_map,
        )
        sink = FilebeatFileSink(log_path, rotation="25 MB")
        logger.add(
            sink=sink,
            filter=request_filter,
            format=json_formatter.format,
            enqueue=config.filebeat.enqueue,
            diagnose=config.filebeat.diagnose,
        )

    print("[zoelogger] logging configured.")
    # print('logger config', logger, id(logger))


def config_logging(
    log_ip: str,
    log_port: int,
    log_index_name: str,
    app_name: str,
    log_level: Optional[str] = None,
    span_id_getter: Optional[Callable[[], str]] = None,
    trace_id_getter: Optional[Callable[[], str]] = None,
    override_logger_names: Optional[List[str]] = None,
    enqueue=False,
    diagnose=True,
    async_sender=False,
    async_concurrency=1,
    level_map=default_level_map,
):
    """
    :param log_ip: 日志服务器ip
    :param log_port: 日志服务器端口
    :param log_index_name: 存储到elasticsearch的index名称.
    约定：一个大项目中所有服务都使用相同的前缀，后面放自己项目名
    如：健看管理大项目里, 用户行为统计 的index_name可以叫 health_manage:conduct_audition
    这样kibana里可以用前缀 health_manage:* 来查询大项目里所有服务的日志，用一个traceId检索.
    运维说先这样设计 未来看看会不会有更好的方案
    :param app_name: 应用名称
    :param log_level: 日志级别 info, debug, error, warn, 默认info
    :param span_id_getter: span_id getter 函数
    :param trace_id_getter: trace_id getter 函数
    :param override_logger_names: 覆盖其他框架中使用的logger
    :param enqueue: @see https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger.add
    :param diagnose: 抛异常时，是否展示变量的值
    :param async_sender: 是否异步发送日志
    :param async_concurrency: 异步发送日志的并发数
    :param level_map: 日志级别映射
    :return:
    """
    for k, v in level_map.items():
        assert v in allowed_levels, f"{k}: {v} is not in allowed_levels"

    levels = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "warn": logging.WARN,
        "error": logging.ERROR,
    }
    if log_level:
        _logging_level = levels.get(log_level.lower(), logging.INFO)
    else:
        _logging_level = logging.INFO

    # 兼容使用 logging.getLogger(__name__) 的方式
    root = logging.getLogger()
    root.setLevel(_logging_level)
    root.handlers = [InterceptHandler(level=_logging_level)]

    # override_logger_names = ("uvicorn.asgi", "uvicorn.access", "uvicorn.error", 'uvicorn')
    if override_logger_names:
        for logger_name in override_logger_names:
            logging_logger = logging.getLogger(logger_name)
            logging_logger.handlers.clear()
            logging_logger.handlers.append(InterceptHandler(level=_logging_level))
            logging_logger.propagate = False  # 阻止日志传递给父级handler

    def request_filter(record) -> bool:
        span_id = ""
        if span_id_getter:
            span_id = span_id_getter()
        record.get("extra")["span_id"] = span_id
        trace_id = ""
        if trace_id_getter:
            trace_id = trace_id_getter()
        record.get("extra")["trace_id"] = trace_id
        return True

    json_formatter = LogStashLogFormatter(
        app_name=app_name, log_index_name=log_index_name, level_map=level_map
    )
    if async_sender:
        sinker = AsyncLogStashSink(
            host=log_ip,
            port=log_port,
            formatter=json_formatter,
            concurrency=async_concurrency,
        )
    else:
        sinker = SyncLogStashSink(host=log_ip, port=log_port, formatter=json_formatter)
    # 使用 logger.config 而不是 logger.add
    # logger.config 可以替换此前配置的 sinker

    # logger.add(sinker, enqueue=True, filter=request_filter)
    # logger.add(sys.stdout)

    handlers = [
        {
            "sink": sys.stderr,
            "level": _logging_level,
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} {level} {extra[trace_id]} {message}",
            "filter": request_filter,
        },
        {
            "sink": sinker,
            "enqueue": enqueue,
            "level": _logging_level,
            "filter": request_filter,
            "diagnose": diagnose,
        },
    ]

    # 仅限在本机调试情况下启用文件日志
    file_path = os.getenv("DEBUG_LOG_FILE_PATH")
    if file_path:
        print(f"DEBUG_LOG_FILE_PATH enabled. file_path: {file_path}")
        handlers.append(
            {
                "sink": file_path,
                "level": logging.DEBUG,
            }
        )

    logger.configure(handlers=handlers)

    check_tcp(log_ip, log_port)
