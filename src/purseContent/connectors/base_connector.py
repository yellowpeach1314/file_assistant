from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from ..document_model import Document

class BaseConnector(ABC):
    """数据源连接器基类"""
    
    def __init__(self):
        self.source_type = self.__class__.__name__.lower().replace('connector', '')
        
    @abstractmethod
    def fetch_content(self, identifier: str) -> Optional[Document]:
        """获取内容的抽象方法"""
        pass
        
    @abstractmethod
    def parse_content(self, raw_content: Any) -> str:
        """解析内容的抽象方法"""
        pass
        
    def generate_id(self, identifier: str) -> str:
        """生成内部ID"""
        return f"{self.source_type}:{identifier}"