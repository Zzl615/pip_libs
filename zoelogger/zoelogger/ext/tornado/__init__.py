import json
import logging

from loguru import logger

__all__ = ["log_function"]


def _decode_my_arguments(handler, arguments):
    try:
        out_put_dict = {}
        for (key, value) in list(arguments.items()):
            out_put_dict["%s" % (key,)] = "%s" % value
        return out_put_dict
    except Exception:
        logging.info("_decode_my_arguments failed.", exc_info=True)
        out_put_dict = {}
        return out_put_dict


def log_function(handler) -> None:
    request_time = handler.request.request_time()
    body = handler.request.body
    if "upload" in handler.request.uri:
        body = "<large request body>"

    if isinstance(body, bytes):
        body = body.decode("utf-8", "ignore")

    status = handler.get_status()
    method = handler.request.method
    uri = handler.request.uri
    arguments = json.dumps(
        _decode_my_arguments(handler, handler.request.arguments),
        ensure_ascii=False,
    )

    request_time_ms = int(request_time * 1000)
    ip = handler.request.remote_ip
    real_ip = handler.request.headers.get("X-Real-Ip", "") or ip
    user_agent = handler.request.headers.get("User-Agent", "")

    _logger = logger.bind(
        request=dict(
            status=status,
            method=method,
            uri=uri,
            arguments=arguments,
            request_time_ms=request_time_ms,
            body=body,
            real_ip=real_ip,
            user_agent=user_agent,
        )
    )

    if handler.get_status() < 400:
        log_method = _logger.info
    elif handler.get_status() < 500:
        log_method = _logger.warning
    else:
        log_method = _logger.error

    log_method(
        "ACCESS: {}\t{}\t{}\t{}\t{}\t{}ms".format(
            handler.get_status(),
            handler.request.method,
            handler.request.uri,
            arguments,
            body,
            int(request_time * 1000),
        )
    )
