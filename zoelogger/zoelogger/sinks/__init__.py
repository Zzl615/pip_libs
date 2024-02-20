from zoelogger.sinks.logstash import (
    AsyncLogStashSink,
    LogStashLogFormatter,
)


def make_async_tcp_logstash_sink(
    host: str, port: int, concurrency: int = 1
) -> AsyncLogStashSink:
    sink = AsyncLogStashSink(
        host=host,
        port=port,
        formatter=LogStashLogFormatter(),
        concurrency=concurrency,
    )
    return sink


#
#
# from loguru import logger
# from typing import cast
# import asyncio
# from types import FrameType
# import logging
# class InterceptHandler(logging.Handler):
#     """
#     logging 转发到 loguru
#     """
#
#     def emit(self, record: logging.LogRecord) -> None:
#         try:
#             level = logger.level(record.levelname).name
#         except ValueError:
#             level = str(record.levelno)
#
#         frame, depth = logging.currentframe(), 2
#         while frame.f_code.co_filename == logging.__file__:
#             frame = cast(FrameType, frame.f_back)
#             depth += 1
#
#         logger.opt(depth=depth, exception=record.exc_info).log(
#             level,
#             record.getMessage(),
#         )
#
#
# async def main():
#     import sys
#     import logging
#     root = logging.getLogger()
#     root.setLevel(logging.INFO)
#     root.handlers = [InterceptHandler(level=logging.INFO)]
#     formatter = LogStashSinkFormatter(app_name="test_app", log_index_name="test_app_index")
#     sink = AsyncLogStashSink(host='127.0.0.1', port=12345, formatter=formatter, concurrency=1)
#     test_logger = logging.getLogger('test_logger')
#     test_logger.handlers.clear()
#     test_logger.handlers.append(InterceptHandler(level=logging.INFO))
#     test_logger.propagate = False
#     logger.configure(handlers=[
#         {
#             'sink': sys.stdout,
#             'level': logging.INFO,
#         },
#         {
#             'sink': sink,
#             'level': logging.INFO,
#         }
#     ])
#     test_logger = logging.getLogger('test_logger')
#     test_logger.info("asdfdsaasdfsa")
#     test_logger.error("hahaha")
#     try:
#         1/0
#     except:
#         test_logger.exception("hehehe")
#     await asyncio.sleep(1000)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
#
