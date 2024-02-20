import json
import logging
import urllib.parse
from datetime import timezone
from typing import Dict, Tuple, Optional

from dateutil import tz
from loguru._file_sink import FileSink

from zoelogger.level import default_level_map
from zoelogger.sinkguru import LogFormatter, Message
from zoelogger.sinks.common import elk_format


class FilebeatLogFormatter(LogFormatter):
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

    def format(self, record) -> str:
        json_record = elk_format(
            record, self._level_map, self._app_name, self._log_index_name
        )
        txt = urllib.parse.quote_plus(json.dumps(json_record))
        return txt


class FilebeatFileSink(FileSink):
    def write(self, message):
        message = urllib.parse.unquote_plus(message) + "\n"
        # message = "{%s}\n" % (message,)
        super().write(message)
