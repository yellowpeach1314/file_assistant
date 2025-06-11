from abc import ABC, abstractmethod
from typing import Optional
import requests

class BaseLLM(ABC):
    """
    抽象基类，定义了所有大模型调用类应遵循的接口。
    """

    def __init__(self, api_key: str, model_name: str, api_endpoint: Optional[str] = None):
        """
        初始化基类。
        :param api_key: API 密钥。
        :param model_name: 模型名称。
        :param api_endpoint: API 端点。
        """
        if not api_key:
            raise ValueError("API 密钥不能为空。")
        if not model_name:
            raise ValueError("模型名称不能为空。")

        self.api_key = api_key
        self.model_name = model_name
        self.api_endpoint = api_endpoint

    @abstractmethod
    async def call_llm_api(self, messages: list, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        抽象方法：调用大模型 API。
        所有继承此基类的具体 LLM 类都必须实现此方法。
        :param messages: 消息列表。
        :param max_tokens: 最大生成 token 数。
        :param temperature: 温度参数。
        :return: LLM 的响应文本。
        """
        pass

    @abstractmethod
    def _parse_llm_response(self, response: requests.Response) -> str:
        """
        抽象方法：解析大模型 API 的响应。
        所有继承此基类的具体 LLM 类都必须实现此方法。
        :param response: requests.Response 对象。
        :return: 解析出的文本内容。
        """
        pass