"""DeepSeek API接口"""

import requests
import os
import logging
from typing import List, Dict, Any
from config.settings import API_CONFIG

logger = logging.getLogger(__name__)

class DeepSeekAPI:
    """DeepSeek API客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or API_CONFIG["deepseek"]["api_key"]
        self.base_url = API_CONFIG["deepseek"]["base_url"]
        self.model = API_CONFIG["deepseek"]["model"]
        
        if not self.api_key:
            logger.warning("未设置DeepSeek API密钥")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat(self, 
             prompt: str, 
             max_tokens: int = None, 
             temperature: float = None) -> str:
        """
        单轮对话
        Args:
            prompt: 输入提示
            max_tokens: 最大token数
            temperature: 温度参数
        Returns:
            API回应
        """
        if not self.api_key:
            logger.error("API密钥未设置")
            return "DeepSeek API密钥未设置"
        
        try:
            # 添加重试机制
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    data = {
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": max_tokens or API_CONFIG["deepseek"]["max_tokens"],
                        "temperature": temperature or API_CONFIG["deepseek"]["temperature"]
                    }
                    
                    timeout = 60 if attempt == 0 else 90  # 重试时增加超时
                    response = requests.post(
                        f"{self.base_url}/v1/chat/completions",
                        headers=self.headers,
                        json=data,
                        timeout=timeout
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    reply = result['choices'][0]['message']['content']
                    logger.debug(f"DeepSeek API回应: {reply[:100]}...")
                    
                    return reply.strip()
                    
                except requests.exceptions.Timeout as e:
                    if attempt < max_retries:
                        logger.warning(f"API超时，第{attempt + 1}次重试...")
                        continue
                    else:
                        raise e
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries:
                        logger.warning(f"API请求失败，第{attempt + 1}次重试: {e}")
                        continue
                    else:
                        raise e
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return f"API请求失败: {str(e)}"
        except KeyError as e:
            logger.error(f"API响应格式错误: {e}")
            return "API响应格式错误"
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return f"API调用失败: {str(e)}"
    
    def chat_with_history(self, 
                         messages: List[Dict[str, str]], 
                         max_tokens: int = None,
                         temperature: float = None) -> str:
        """
        多轮对话
        Args:
            messages: 对话历史，格式 [{"role": "user/assistant", "content": "..."}]
            max_tokens: 最大token数
            temperature: 温度参数
        Returns:
            API回应
        """
        if not self.api_key:
            logger.error("API密钥未设置")
            return "DeepSeek API密钥未设置"
        
        try:
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or API_CONFIG["deepseek"]["max_tokens"],
                "temperature": temperature or API_CONFIG["deepseek"]["temperature"]
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            reply = result['choices'][0]['message']['content']
            return reply.strip()
            
        except Exception as e:
            logger.error(f"多轮对话API调用失败: {e}")
            return f"API调用失败: {str(e)}"
    
    def is_available(self) -> bool:
        """检查API是否可用"""
        if not self.api_key:
            return False
        
        try:
            response = self.chat("测试", max_tokens=10)
            return not response.startswith("API")  # 不是错误消息
        except:
            return False

# 全局API实例
_deepseek_api = None

def get_deepseek_api() -> DeepSeekAPI:
    """获取全局DeepSeek API实例"""
    global _deepseek_api
    if _deepseek_api is None:
        _deepseek_api = DeepSeekAPI()
    return _deepseek_api
