import logging

CRITICAL = (2, "Critical")
ERROR = (3, "Error")
WARNING = (4, "Warning")
INFO = (6, "Informational")
DEBUG = (7, "Debug")

allowed_levels = [CRITICAL, ERROR, WARNING, INFO, DEBUG]

default_level_map = {
    logging.CRITICAL: CRITICAL,
    logging.ERROR: ERROR,
    logging.WARNING: WARNING,
    logging.INFO: INFO,
    logging.DEBUG: DEBUG,
}


error_as_critical_level_map = {
    logging.CRITICAL: CRITICAL,
    logging.ERROR: CRITICAL,
    logging.WARNING: WARNING,
    logging.INFO: INFO,
    logging.DEBUG: DEBUG,
}
