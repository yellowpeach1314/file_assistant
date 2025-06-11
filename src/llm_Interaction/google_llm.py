import os
import json
import requests
from typing import Optional
from .base_llm import BaseLLM

# 导入 Google GenAI 库，如果需要直接使用其客户端
# from google import genai

class GoogleLLM(BaseLLM):
    """
    GoogleLLM 类，负责与 Google Gemini API 进行交互。
    继承自 BaseLLM，实现具体的 API 调用和响应解析逻辑。
    """

    def __init__(self, api_key: str, model_name: str, api_endpoint: Optional[str] = None):
        """
        初始化 GoogleLLM 实例。
        :param api_key: Google API 密钥。
        :param model_name: 要使用的 Google 模型名称（例如 'gemini-pro'）。
        :param api_endpoint: Google API 端点。如果未提供，将使用默认端点。
        """
        super().__init__(api_key, model_name, api_endpoint)
        if not self.api_endpoint:
            # 默认的 Google Gemini API 端点，需要根据实际模型和版本调整
            self.api_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # 如果需要使用 Google GenAI 客户端库，可以在这里初始化
        # self.client = genai.Client(api_key=self.api_key)

    async def call_llm_api(self, messages: list, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        调用 Google Gemini API。
        :param messages: 消息列表，格式应符合 Google Gemini API 要求。
        :param max_tokens: 最大生成 token 数。
        :param temperature: 温度参数。
        :return: LLM 的响应文本。
        """
        headers = {"Content-Type": "application/json"}
        
        # 将通用消息格式转换为 Google Gemini API 所需的 'contents' 格式
        # Google Gemini API 通常使用 'parts' 而不是 'messages'，且结构不同
        formatted_contents = []
        for msg in messages:
            # 假设消息格式为 {'role': 'user', 'content': '...'}
            # Google Gemini API 的 'contents' 结构可能更复杂，这里是一个简化示例
            if msg['role'] == 'user':
                formatted_contents.append({"role": "user", "parts": [{"text": msg['content']}]})
            elif msg['role'] == 'model':
                formatted_contents.append({"role": "model", "parts": [{"text": msg['content']}]})
            # 根据需要处理其他角色，例如 'system'

        payload = {
            "contents": formatted_contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature,
            }
            # 可以添加其他配置，例如 safetySettings
        }
        
        # 替换API端点中的模型名称和API密钥
        endpoint = self.api_endpoint.format(model=self.model_name, api_key=self.api_key)

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()  # 检查 HTTP 错误状态码
            return self._parse_llm_response(response)
        except requests.exceptions.Timeout:
            raise requests.exceptions.RequestException("API 请求超时。请检查网络连接或稍后重试。")
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.RequestException("网络连接错误。请检查您的互联网连接。")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_message = f"API 请求失败，状态码：{status_code}。错误详情：{e.response.text}"
            if status_code == 401:
                error_message += " (无效的 API 密钥)"
            elif status_code == 429:
                error_message += " (API 限流，请求过多)"
            raise requests.exceptions.RequestException(error_message)
        except json.JSONDecodeError:
            raise json.JSONDecodeError("无法解析 API 响应为 JSON。响应内容：\n" + response.text)
        except Exception as e:
            raise ValueError(f"调用 Google Gemini API 时发生未知错误：{e}")

    def _parse_llm_response(self, response: requests.Response) -> str:
        """
        解析 Google Gemini API 的响应。
        :param response: requests.Response 对象。
        :return: 解析出的文本内容。
        """
        try:
            response_json = response.json()
            # Google Gemini 的响应通常在 'candidates'[0]['content']['parts'][0]['text']
            if "candidates" in response_json and len(response_json["candidates"]) > 0:
                first_candidate = response_json["candidates"][0]
                if "content" in first_candidate and "parts" in first_candidate["content"] and len(first_candidate["content"]["parts"]) > 0:
                    return first_candidate["content"]["parts"][0]["text"]
            
            raise ValueError(f"无法从 Google Gemini API 响应中找到预期的内容。响应结构：{response_json}")
        except json.JSONDecodeError:
            raise json.JSONDecodeError("解析 Google Gemini API 响应时发生 JSON 错误。")
        except KeyError as e:
            raise ValueError(f"Google Gemini API 响应缺少预期的键：{e}。完整响应：{response.text}")
        except Exception as e:
            raise ValueError(f"解析 Google Gemini 响应时发生未知错误：{e}")

# 示例用法（通常在 LLMCoordinator 中调用，这里仅为独立测试示例）
if __name__ == "__main__":
    # 请替换为您的实际 API 密钥和模型名称
    api_key = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
    model_name = "gemini-pro"

    google_llm = GoogleLLM(api_key=api_key, model_name=model_name)

    async def main():
        try:
            response_text = await google_llm.call_llm_api(
                messages=[{"role": "user", "content": "你好，请介绍一下你自己。"}]
            )
            print(f"Google Gemini 响应: {response_text}")
        except Exception as e:
            print(f"发生错误: {e}")

    import asyncio
    asyncio.run(main())