from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json

@dataclass
class Document:
    """统一内部文档表示格式"""
    id: str  # 内部生成的唯一标识符
    source_type: str  # 数据来源类型
    source_identifier: str  # 原始标识符
    title: str  # 文档标题
    raw_content: Any  # 原始内容
    cleaned_text: str  # 清洗后的纯文本
    url: Optional[str] = None  # 可选的URL
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据
    ingestion_timestamp: Optional[datetime] = None  # 摄取时间
    dependencies: Optional[Dict[str, Dict[str, Any]]] = None  # 文档依赖关系
    
    def __post_init__(self):
        """初始化后的处理"""
        if self.metadata is None:
            self.metadata = {}
        if self.dependencies is None:
            self.dependencies = {}
        if self.ingestion_timestamp is None:
            self.ingestion_timestamp = datetime.now()
            
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'source_type': self.source_type,
            'source_identifier': self.source_identifier,
            'title': self.title,
            'raw_content': self.raw_content,
            'cleaned_text': self.cleaned_text,
            'url': self.url,
            'metadata': self.metadata,
            'dependencies': self.dependencies,
            'ingestion_timestamp': self.ingestion_timestamp.isoformat() if self.ingestion_timestamp else None
        }