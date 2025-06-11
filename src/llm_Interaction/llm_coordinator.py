import os
import requests
import json
from typing import Optional, Dict, Type
from .base_llm import BaseLLM # 导入BaseLLM基类

class LLMCoordinator:
    """
    LLMCoordinator 负责调度大模型调用过程，支持用户设置 API 密钥并将其分配给
    继承统一基类的具体大模型调用类。
    """
    _llm_implementations: Dict[str, Type[BaseLLM]] = {}

    @classmethod
    def register_llm(cls, model_name: str, llm_class: Type[BaseLLM]):
        """
        注册一个LLM实现类。
        :param model_name: 模型的名称，例如 'google-gemini', 'openai-gpt'
        :param llm_class: 继承自 BaseLLM 的具体LLM类
        """
        if not issubclass(llm_class, BaseLLM):
            raise TypeError(f"注册的类 {llm_class.__name__} 必须继承自 BaseLLM")
        cls._llm_implementations[model_name] = llm_class

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        初始化 LLMCoordinator 实例。
        :param api_keys: 一个字典，包含不同LLM的API密钥，例如 {'google': 'YOUR_GOOGLE_API_KEY'}
        """
        self.api_keys = api_keys if api_keys is not None else {}

    def get_llm_instance(self, model_name: str, **kwargs) -> BaseLLM:
        """
        根据模型名称获取对应的LLM实例。
        :param model_name: 模型的名称，例如 'google-gemini-pro'
        :param kwargs: 传递给具体LLM类构造函数的额外参数
        :return: 对应的 BaseLLM 实例
        """
        # 从注册的实现中查找最匹配的LLM类
        llm_class = None
        for registered_model_name, registered_llm_class in self._llm_implementations.items():
            if model_name.startswith(registered_model_name):
                llm_class = registered_llm_class
                break
        
        if llm_class is None:
            raise ValueError(f"不支持的模型名称: {model_name}. 请确保已注册该模型的实现。")

        # 尝试从环境变量或传入的api_keys中获取API密钥
        # 这里需要根据具体的LLM实现来确定如何获取和传递API密钥
        # 例如，如果GoogleLLM需要'google_api_key'，则从self.api_keys['google']获取
        api_key_for_llm = None
        # 这是一个简化的示例，实际应用中需要更复杂的逻辑来匹配API密钥
        # 比如，可以约定每个LLM类有一个静态方法来指示它需要的API密钥类型
        if 'google' in model_name.lower() and 'google' in self.api_keys:
            api_key_for_llm = self.api_keys['google']
        elif 'openai' in model_name.lower() and 'openai' in self.api_keys:
            api_key_for_llm = self.api_keys['openai']
        # 也可以从环境变量中获取
        elif os.getenv(f"{model_name.upper().replace('-', '_')}_API_KEY"):
            api_key_for_llm = os.getenv(f"{model_name.upper().replace('-', '_')}_API_KEY")
        
        if api_key_for_llm:
            kwargs['api_key'] = api_key_for_llm

        return llm_class(model_name=model_name, **kwargs)

    async def generate_text(self, model_name: str, messages: list, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        使用指定模型生成文本。
        :param model_name: 要使用的模型名称。
        :param messages: 消息列表。
        :param max_tokens: 最大生成token数。
        :param temperature: 温度参数。
        :return: 生成的文本。
        """
        llm_instance = self.get_llm_instance(model_name)
        return await llm_instance.call_llm_api(messages, max_tokens, temperature)