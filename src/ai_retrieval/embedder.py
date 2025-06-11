from abc import ABC, abstractmethod
from typing import List, Optional
from .models import TextChunk, ChunkWithEmbedding
from sentence_transformers import SentenceTransformer # 导入 SentenceTransformer

# 这是一个示例配置，实际中你可能需要从配置文件或环境变量加载
EMBEDDING_MODEL_CONFIG = {
    "provider": "sentence_transformers", # 'openai', 'sentence_transformers', etc.
    "model_name": "all-MiniLM-L6-v2" # if sentence_transformers
}

class BaseEmbeddingModel(ABC):
    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        pass

class PlaceholderEmbeddingModel(BaseEmbeddingModel):
    """
    一个占位符嵌入模型，返回固定长度的零向量。
    实际使用时应替换为真正的嵌入模型。
    """
    def __init__(self, dimension: int = 768): # 示例维度
        self.dimension = dimension
        print(f"WARNING: Using PlaceholderEmbeddingModel. Replace with a real embedding model for production.")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self.dimension for _ in texts]

class SentenceTransformerEmbeddingModel(BaseEmbeddingModel):
    """
    使用 sentence-transformers 库的嵌入模型。
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        print(f"Using SentenceTransformer model: {model_name}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # sentence-transformers 的 encode 方法直接返回 numpy 数组，需要转换为 List[List[float]]
        embeddings = self.model.encode(texts).tolist()
        return embeddings

class EmbeddingComponent:
    """
    向量嵌入组件，负责将文本块转化为向量。
    """
    def __init__(self, embedding_model: Optional[BaseEmbeddingModel] = None):
        if embedding_model:
            self.model = embedding_model
        else:
            provider = EMBEDDING_MODEL_CONFIG.get("provider")
            model_name = EMBEDDING_MODEL_CONFIG.get("model_name")

            if provider == "openai":
                # self.model = OpenAIEmbeddingModel(model_name=model_name)
                raise NotImplementedError("OpenAIEmbeddingModel not implemented yet.")
            elif provider == "sentence_transformers":
                self.model = SentenceTransformerEmbeddingModel(model_name=str(model_name))
            else:
                self.model = PlaceholderEmbeddingModel()


    def embed_chunks(self, chunks: List[TextChunk]) -> List[ChunkWithEmbedding]:
        """
        将文本块列表转化为带嵌入的文本块列表。

        Args:
            chunks: 文本块列表。

        Returns:
            带嵌入的文本块列表。
        """
        if not chunks:
            return []

        texts_to_embed = [chunk.text for chunk in chunks]
        embeddings = self.model.get_embeddings(texts_to_embed)

        chunks_with_embeddings = []
        for chunk, embedding in zip(chunks, embeddings):
            chunks_with_embeddings.append(
                ChunkWithEmbedding(
                    **chunk.model_dump(), # 解包 TextChunk 的字段
                    embedding=embedding
                )
            )
        return chunks_with_embeddings

    def embed_query(self, query_text: str) -> List[float]:
        """
        将查询文本转化为向量。
        """
        if not query_text:
            return []
        return self.model.get_embeddings([query_text])[0]

# TODO: 实现具体的 EmbeddingModel 类，例如:
# class OpenAIEmbeddingModel(BaseEmbeddingModel): ...
# 并根据配置动态加载。