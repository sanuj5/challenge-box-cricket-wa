import logging
logger = logging.getLogger()


class Logger:
    @staticmethod
    def info(message, *args, **kwargs):
        logger.info(message, *args, **kwargs)

    @staticmethod
    def debug(message, *args, **kwargs):
        logger.debug(message, *args, **kwargs)

    @staticmethod
    def error(message, *args, **kwargs):
        logger.error(message, *args, **kwargs)