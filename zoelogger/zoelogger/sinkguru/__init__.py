from loguru._handler import Message
from zoelogger.sinkguru.abcs import LogFormatter, LogBuffer, LogSender


class LogStashSink:
    def __init__(self, formatter: LogFormatter, sender: LogSender) -> None:
        self._formatter = formatter
        self._sender = sender

    async def __call__(self, message: Message) -> None:
        formatted = self._formatter.format(message)
        await self._sender.send(formatted)
