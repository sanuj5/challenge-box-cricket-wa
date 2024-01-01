import logging
logging.root.handlers = []
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)


class Logger:
    @staticmethod
    def info(message, *args, **kwargs):
        logging.info(message, *args, **kwargs)

    @staticmethod
    def debug(message, *args, **kwargs):
        logging.debug(message, *args, **kwargs)

    @staticmethod
    def error(message, *args, **kwargs):
        logging.error(message, *args, **kwargs)