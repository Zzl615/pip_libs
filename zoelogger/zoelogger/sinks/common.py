import logging
from datetime import timezone


def elk_format(message, _level_map, _app_name, _log_index_name):
    if isinstance(message, dict):
        record = message
    else:
        record = message.record
    stack_trace = None
    if not record.get("exception"):
        message = record.get("message")
        message = str(message)
    else:
        message = str(message)
        exc_index = message.find("Traceback (most recent call last):")
        if exc_index >= 0:
            stack_trace = message[exc_index:]
            message = message[:exc_index]

    log_time = (
        record.get("time")
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
        .isoformat(timespec="milliseconds")
        + "Z"
    )
    level = record.get("level").no
    if level not in _level_map:
        level = logging.INFO
        # logging.warning(f'unknown level: {record.get("level")}')
    level_name = _level_map[level][1]
    level_number = _level_map[level][0]
    instance_descriptor = record.get("extra").get("instance_descriptor")
    sampled = bool(record.get("extra").get("trace_sampled"))
    sampled = "true" if sampled else "false"
    logger_name = record.get("name")
    if "logger_name" in record.get("extra"):
        logger_name = record.get("extra").get("logger_name")
    request = record.get("extra").get("request", None)
    json_record = {
        "appName": _app_name,
        "instance_descriptor": instance_descriptor,
        "@timestamp": log_time,
        "LoggerName": logger_name,
        "SourceMethodName": record.get("function"),
        "spanId": record.get("extra").get("span_id"),
        "traceId": record.get("extra").get("trace_id"),
        "sampled": sampled,
        "SourceSimpleClassName": record.get("module"),
        "message": message,
        "parentId": record.get("extra").get("parent_id"),
        "SourceClassName": record.get("module"),
        "indexName": _log_index_name,
        "facility": "loguru",
        "Severity": level_name,
        "Thread": f"{record.get('thread').name}-{record.get('thread').id}",
        "Process": f"{record.get('process').name}-{record.get('process').id}",
        "line": f"{record.get('name')}#{record.get('line')}",
        "level": level_number,
        "@version": "1",
        "host": record.get("extra").get("clientip"),
        "filepath": f"{record.get('file').path}",
        "StackTrace": stack_trace,
        "LoggerFile": record.get("file").name,
        "IsRequestLog": 1 if request else 0,
        "request": request,
        "extraData": record.get("extra").get("extraData"),
        "logType": record.get("extra").get("logType"),
    }
    return json_record
