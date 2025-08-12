from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging
from config.settings import EMBEDDING_CONFIG

logger = logging.getLogger(__name__)

class EmbeddingService:
    """嵌入服务 - 使用本地bge-small-zh-v1.5模型"""
    
    def __init__(self):
        """初始化嵌入服务"""
        try:
            model_path = EMBEDDING_CONFIG["model_path"]
            logger.info(f"尝试加载本地嵌入模型: {model_path}")
            self.model = SentenceTransformer(model_path)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"本地嵌入模型加载成功，维度: {self.dimension}")
        except Exception as e:
            logger.warning(f"本地嵌入模型加载失败: {e}")
            logger.info("尝试加载在线备用模型...")
            try:
                fallback_model = EMBEDDING_CONFIG["fallback_model"]
                self.model = SentenceTransformer(fallback_model)
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"在线备用模型加载成功，维度: {self.dimension}")
            except Exception as e2:
                logger.error(f"所有嵌入模型加载失败: {e2}")
                raise RuntimeError("无法加载任何嵌入模型")
    
    def encode_single(self, text: str) -> np.ndarray:
        """
        对单个文本进行嵌入
        Args:
            text: 输入文本
        Returns:
            嵌入向量
        """
        try:
            # 预处理文本
            text = self._preprocess_text(text)
            embeddings = self.model.encode(text)
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"文本嵌入失败: {e}")
            # 返回零向量作为fallback
            return np.zeros(self.dimension, dtype=np.float32)
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        批量文本嵌入
        Args:
            texts: 文本列表
        Returns:
            嵌入向量数组
        """
        try:
            processed_texts = [self._preprocess_text(text) for text in texts]
            embeddings = self.model.encode(processed_texts)
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"批量嵌入失败: {e}")
            return np.zeros((len(texts), self.dimension), dtype=np.float32)
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        if not text:
            return ""
        
        # 移除多余空格
        text = ' '.join(text.split())
        
        # 截断过长文本 (BGE模型最大512 tokens)
        if len(text) > 400:  # 保守估计
            text = text[:400] + "..."
        
        return text
    
    def get_dimension(self) -> int:
        """获取嵌入维度"""
        return self.dimension

# 全局嵌入服务实例
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """获取全局嵌入服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
