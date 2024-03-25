import time
from loguru import logger
from pathlib import Path

# 获取当前文件路径的父目录
project_path = Path.cwd()
log_path = Path(project_path, "logs")
t = time.strftime("%Y_%m_%d")


class Loggings:
    __instance = None
    logger.add(
        f"{log_path}/interface_info_{t}.log",
        level="INFO",
        rotation="500MB",
        encoding="utf-8",
        enqueue=True,
        retention="10 days",
    )
    logger.add(
        f"{log_path}/interface_debug_{t}.log",
        level="DEBUG",
        rotation="500MB",
        encoding="utf-8",
        enqueue=True,
        retention="10 days",
        filter=lambda record: record["level"].name == "DEBUG",
    )
    logger.add(
        f"{log_path}/interface_warning_{t}.log",
        level="WARNING",
        rotation="500MB",
        encoding="utf-8",
        enqueue=True,
        retention="10 days",
    )
    logger.add(
        f"{log_path}/interface_error_{t}.log",
        level="ERROR",
        rotation="500MB",
        encoding="utf-8",
        enqueue=True,
        retention="10 days",
    )

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Loggings, cls).__new__(cls, *args, **kwargs)

        return cls.__instance

    def info(self, msg):
        return logger.info(msg)

    def debug(self, msg):
        return logger.debug(msg)

    def warning(self, msg):
        return logger.warning(msg)

    def error(self, msg):
        return logger.error(msg)
