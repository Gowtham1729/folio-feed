import logging

from pythonjsonlogger import jsonlogger


def get_logger(name=None, level=logging.INFO, log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Specify the log record attributes to include in the logs
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
