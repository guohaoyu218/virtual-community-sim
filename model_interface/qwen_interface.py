import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from config.settings import MODEL_CONFIG
import logging

logger = logging.getLogger(__name__)

class QwenInterface:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda"  # 强制CUDA
        self.quantized = False
        self._load_model()
        
    def _load_model(self):
        """强制GPU加载模型"""
        try:
            model_path = MODEL_CONFIG["local_model_path"]
            logger.info(f"强制GPU加载模型: {model_path}")
            
            # 检查CUDA
            if not torch.cuda.is_available():
                raise RuntimeError("❌ 没有GPU就别跑大模型！")
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path, trust_remote_code=True
            )
            
            # 修复pad_token问题
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 直接FP16 GPU加载 - 简单粗暴
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16,
                device_map="cuda"  # 直接GPU
            )
            
            # 验证在GPU上
            device = str(next(self.model.parameters()).device)
            if "cuda" not in device:
                raise RuntimeError(f"模型在{device}上，不是GPU！")
            
            logger.info("✅ 模型成功加载到GPU")
            
        except Exception as e:
            logger.error(f"GPU加载失败: {e}")
            raise
    
    def chat(self, prompt: str, max_tokens: int = None, temperature: float = 0.7) -> str:
        """GPU推理"""
        try:
            if max_tokens is None:
                max_tokens = MODEL_CONFIG["default_max_tokens"]
            
            # 简化prompt，避免过度指令化
            enhanced_prompt = prompt
            
            # 强制GPU，添加attention_mask
            inputs = self.tokenizer(
                enhanced_prompt, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=1024  # 减少输入长度提高速度
            ).to('cuda')
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.8,  # 添加top_p采样
                    repetition_penalty=1.1,  # 减少重复
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:], 
                skip_special_tokens=True
            )
            
            torch.cuda.empty_cache()
            return response.strip()
            
        except Exception as e:
            logger.error(f"GPU推理失败: {e}")
            return f"抱歉，AI系统暂时遇到了技术问题：{str(e)}"
    
    def get_model_info(self) -> dict:
        """模型信息"""
        actual_device = str(next(self.model.parameters()).device) if self.model else "unknown"
        return {
            "device": "cuda",
            "actual_device": actual_device,
            "model_loaded": self.model is not None
        }

# 全局实例
_qwen_model = None

def get_qwen_model() -> QwenInterface:
    global _qwen_model
    if _qwen_model is None:
        _qwen_model = QwenInterface()
    return _qwen_model