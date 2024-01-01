import logging
import sys

log = logging.getLogger()
log.setLevel(logging.DEBUG)
_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(_format)
log.addHandler(ch)


class Logger:
    @staticmethod
    def info(message, *args, **kwargs):
        log.info(message, *args, **kwargs)

    @staticmethod
    def debug(message, *args, **kwargs):
        log.debug(message, *args, **kwargs)

    @staticmethod
    def error(message, *args, **kwargs):
        log.error(message, *args, **kwargs)