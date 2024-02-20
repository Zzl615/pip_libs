import asyncio

from zoelogger.sinkguru.abcs import LogSender, LogBuffer


class LogStashTcpSender(LogSender):
    def __init__(
        self,
        host: str,
        port: int,
        buffer: LogBuffer,
    ) -> None:
        self._host = host
        self._port = port
        self._writer = None
        self._buffer = buffer
        self._running = True
        self.fail_backoff = 1

    async def connect(self) -> None:
        try:
            _, writer = await asyncio.open_connection(
                self._host,
                self._port,
            )
            self._writer = writer
            self.fail_backoff = 1
        except Exception as e:
            self.fail_backoff = min(self.fail_backoff * 2, 16)
            print(
                f"ERROR:Sender: [{id(self)}] connect error: {e}. Backoff: {self.fail_backoff}"
            )
            self._writer = None
            await asyncio.sleep(self.fail_backoff)

    @property
    def connected(self) -> bool:
        return self._writer is not None

    async def close(self) -> None:
        if self._writer is None:
            return
        self._writer.close()
        await self._writer.wait_closed()
        self._writer = None

    async def send(self, message: bytes) -> None:
        # print(f'Sender:[{id(self)}] send message: {message}')
        if self._writer and self._writer.is_closing():
            self._writer = None
            print(f"Sender:[{id(self)}] reconnect")
        if self._writer is None:
            print(f"Sender:[{id(self)}] connect")
            await self.connect()
        if not self._writer:
            print(f"ERROR:Sender: [{id(self)}] no writer")
            return
        self._writer.write(message)

    async def __call__(self) -> None:
        while self._running:
            buf = await self._buffer.read()
            await self.send(buf)


class LocalBytesBuffer(LogBuffer):
    def __init__(self) -> None:
        self._queue = asyncio.Queue()

    def __len__(self) -> int:
        return self._queue.qsize()

    async def write(self, data: bytes) -> None:
        await self._queue.put(data)

    async def read(self) -> bytes:
        return await self._queue.get()
