import logging
import logging.handlers
import os
from config.settings import LOGGING_CONFIG, DATA_PATHS

def setup_logging():
    """设置项目日志"""
    # 确保日志目录存在
    log_dir = DATA_PATHS["logs_dir"]
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOGGING_CONFIG["level"]))
    
    # 清除现有handlers
    logger.handlers.clear()
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件handler (带轮转)
    log_file = os.path.join(log_dir, "agent_system.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOGGING_CONFIG["max_bytes"],
        backupCount=LOGGING_CONFIG["backup_count"],
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOGGING_CONFIG["format"])
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 减少第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    logger.info("日志系统初始化完成")

if __name__ == "__main__":
    setup_logging()
