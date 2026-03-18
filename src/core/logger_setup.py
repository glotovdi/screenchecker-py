import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def setup_logger(name="screenchecker"):
    config = load_config()
    log_dir = config.get("log_dir", "logs")
    
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger
    
    log_file = os.path.join(log_dir, f"scan_{datetime.now():%Y%m%d}.log")
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
