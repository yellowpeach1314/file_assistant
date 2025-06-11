from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

class TextChunk(BaseModel):
    """
    表示文档中的一个文本块。
    """
    id: str = Field(default_factory=lambda: f"chunk_{uuid.uuid4()}")
    document_id: str  # 原始文档的ID
    text: str  # 文本块的内容
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict) # 可选的元数据，如原始文档的 source_type, 章节信息等
    # 可以添加其他字段，如块的起始/结束位置等

class ChunkWithEmbedding(TextChunk):
    """
    表示带有其向量嵌入的文本块。
    """
    embedding: List[float] # 文本块的向量嵌入