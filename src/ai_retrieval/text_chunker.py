from abc import ABC, abstractmethod
from typing import List, Dict, Any,Optional
from .models import TextChunk

class BaseTextSplitter(ABC):
    """文本分割器的抽象基类"""
    @abstractmethod
    def split_text(self, text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        pass

class CharacterTextSplitter(BaseTextSplitter):
    """
    基于字符数和重叠的简单文本分割器。
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        chunks = []
        if not text:
            return chunks

        start_index = 0
        while start_index < len(text):
            end_index = min(start_index + self.chunk_size, len(text))
            chunk_text = text[start_index:end_index]
            
            chunks.append(
                TextChunk(
                    document_id=document_id,
                    text=chunk_text,
                    metadata=metadata.copy() if metadata else {}
                )
            )
            
            if end_index == len(text):
                break
            start_index += (self.chunk_size - self.chunk_overlap)
            
        return chunks

class TextChunkingComponent:
    """
    文本分块组件，负责将文档文本分割成小块。
    """
    def __init__(self, splitter: Optional[BaseTextSplitter] = None):
        self.splitter = splitter or CharacterTextSplitter() # 默认使用字符分割器

    def chunk_document(self, cleaned_text: str, document_id: str, document_metadata: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """
        将单个文档的 cleaned_text 分割成文本块。

        Args:
            cleaned_text: 文档的纯文本内容。
            document_id: 原始文档的 ID。
            document_metadata: 原始文档的元数据，可以传递给块。

        Returns:
            一个文本块列表。
        """
        if not cleaned_text:
            return []
        
        # 准备块的元数据，可以包含原始文档的一些信息
        chunk_base_metadata = {"original_document_id": document_id}
        if document_metadata:
            # 例如，可以传递 source_type
            if 'source_type' in document_metadata:
                chunk_base_metadata['source_type'] = document_metadata['source_type']
        
        return self.splitter.split_text(text=cleaned_text, document_id=document_id, metadata=chunk_base_metadata)

# TODO: 实现其他分块策略，如基于语义/结构或递归分割。