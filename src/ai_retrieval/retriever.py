from typing import List, Dict, Any, Optional
from .models import TextChunk
from .embedder import EmbeddingComponent
from .vector_db_manager import VectorDBManager

class Retriever:
    """
    检索器，负责接收查询文本，将其向量化，并从向量数据库中检索相关文本块。
    """
    def __init__(self, embedding_component: EmbeddingComponent, vector_db_manager: VectorDBManager):
        self.embedding_component = embedding_component
        self.vector_db_manager = vector_db_manager

    def retrieve_relevant_chunks(self, query_text: str, top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        检索与查询文本相关的文本块。

        Args:
            query_text: 用户的查询文本。
            top_k: 返回最相关块的数量。
            filter_metadata: 用于在向量数据库中过滤的元数据。

        Returns:
            一个字典列表，每个字典包含检索到的块的信息。
            例如: [{"id": "chunk_id_1", "text": "...", "metadata": {...}, "distance": 0.1}, ...]
        """
        if not query_text:
            return []

        # 1. 将查询文本转化为向量
        query_embedding = self.embedding_component.embed_query(query_text)
        if not query_embedding:
            print("Warning: Could not generate embedding for the query.")
            return []

        # 2. 调用向量数据库管理器进行相似度搜索
        similar_chunks_data = self.vector_db_manager.search_similar_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        return similar_chunks_data

# 示例用法 (通常会在服务或应用逻辑中调用)
# if __name__ == '__main__':
#     # 假设已经配置和初始化了组件
#     # from .embedder import PlaceholderEmbeddingModel
#     # embedder_comp = EmbeddingComponent(embedding_model=PlaceholderEmbeddingModel())
#     # vector_db_mgr = VectorDBManager() # 使用默认配置
# 
#     # retriever_instance = Retriever(embedding_component=embedder_comp, vector_db_manager=vector_db_mgr)
#     
#     # 假设有一些数据已经存入向量数据库
#     # ...
# 
#     # query = "告诉我关于狗的知识"
#     # results = retriever_instance.retrieve_relevant_chunks(query)
#     # for res in results:
#     #     print(f"ID: {res['id']}, Distance: {res['distance']:.4f}, Text: {res['text'][:100]}...")