import logging
import sys

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = logging.DEBUG

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        # logging.FileHandler("app.log")  # 필요시 파일 로그 활성화
    ]
)

def get_logger(name):
    return logging.getLogger(name) 