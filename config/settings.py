"""项目配置文件"""
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 模型配置
MODEL_CONFIG = {
    "local_model_path": "./model/Qwen2.5-3B",
    "model_name": "Qwen2.5-3B",
    "device": "auto",
    
    # 设备和内存配置
    "device_map": "auto",
    "trust_remote_code": True,
    "torch_dtype": "float16",
    "low_cpu_mem_usage": True,
    "max_memory": {"0": "5.5GB", "cpu": "4GB"},
    "offload_folder": "./temp_offload",
    
    # 量化配置
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_use_double_quant": False,
    "bnb_4bit_quant_type": "nf4",
    
    # 优化配置
    "use_safetensors": True,
    "cache_dir": None,
    
    # 错误处理
    "loading_retry_attempts": 3,
    "loading_timeout": 300,
    
    # 生成配置 - 降低token以提升速度
    "default_max_tokens": 150,  # 从1000降到150
    "complex_max_tokens": 300,  # 从2000降到300
}

# 嵌入模型配置
EMBEDDING_CONFIG = {
    "model_path": "C:\\Users\\guohaoyu\\.cache\\huggingface\\hub\\models--BAAI--bge-small-zh-v1.5\\snapshots\\7999e1d3359715c523056ef9478215996d62a620",
    "fallback_model": "BAAI/bge-small-zh-v1.5",
    "max_length": 512,
    "batch_size": 16,
}

# Qdrant数据库配置
VECTOR_DB_CONFIG = {
    "use_local": False,
    "host": "localhost",
    "port": 6333,
    "timeout": 30,
    "collection_prefix": "agent_memories",
    
    # 重试配置 - 添加缺失的参数
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "connection_timeout": 10,
    "max_retries": 5,
    
    # 集合配置
    "vector_size": 512,  # 向量维度
    "distance_metric": "cosine",  # 距离度量
    
    # 性能配置
    "batch_size": 100,
    "max_connections": 10,
}

# Agent配置
AGENT_CONFIG = {
    "default_energy": 80,
    "default_location": "家",
    "default_mood": "平静",
    "energy_decay_range": (1, 5),
    "mood_change_probability": 0.3,
    "max_interactions_per_hour": 20,
    
    # 错误处理配置
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "timeout": 30,
    
    # 内存管理配置
    "memory_limit": 100,
    "memory_cleanup_threshold": 0.8,
    
    # 生成配置
    "generation_timeout": 60,
    "max_generation_retries": 2,
}

# 复杂度阈值
COMPLEXITY_THRESHOLDS = {
    "programmer": 0.3,
    "artist": 0.4,
    "teacher": 0.4,
    "student": 0.5,
    "chef": 0.3,
    "businessman": 0.4,
    "default": 0.5,
}

# 可用的心情状态
AVAILABLE_MOODS = ["开心", "平静", "疲惫", "兴奋", "思考中", "创作中", "专注", "沮丧", "好奇"]

# 记忆类型定义
MEMORY_TYPES = {
    "identity": "身份认知",
    "experience": "经历体验", 
    "learning": "学习内容",
    "social": "社交互动",
    "goal": "目标规划",
    "routine": "日常琐事",
    "emotion": "情感记录",
}

# API配置 (从.env文件读取)
API_CONFIG = {
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "max_tokens": 200,  # 从1500降到200
        "temperature": 0.7,
    },
    "use_api_fallback": True,
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "./logs/agent_system.log",
    "max_bytes": 10 * 1024 * 1024,
    "backup_count": 5,
}

# 数据存储路径
DATA_PATHS = {
    "logs_dir": "./logs",
    "agent_profiles": "./data/agent_profiles",
    "interaction_logs": "./data/interactions",
    "cache_dir": "./data/cache",
    "backup_dir": "./data/backup",
}

# Docker相关配置
DOCKER_CONFIG = {
    "qdrant_container_name": "qdrant",
    "auto_create_collections": True,
}

# 自动创建必要的目录
def ensure_directories():
    """确保所有必要的目录存在"""
    for path in DATA_PATHS.values():
        os.makedirs(path, exist_ok=True)

# 初始化时创建目录
ensure_directories()

# 调试信息：检查API密钥是否正确加载
if __name__ == "__main__":
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if api_key:
        print(f"✅ API密钥已加载: {api_key[:10]}...")
    else:
        print("❌ 未找到API密钥")
