from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseCleaner(ABC):
    """文本清洗器基类"""
    
    @abstractmethod
    def clean(self, content: Any) -> str:
        """清洗文本内容的抽象方法
        
        Args:
            content: 原始内容，可以是字符串、字典等任何格式
            
        Returns:
            str: 清洗后的纯文本内容
        """
        pass