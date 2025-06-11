import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from .models import ChunkWithEmbedding
import numpy as np # <--- 添加导入

import os

# 使用绝对路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DB_PATH = os.path.join(project_root, "database/chroma_db_data")
# ChromaDB 配置
# CHROMA_DB_PATH = "../chroma_db_data" # 持久化路径
CHROMA_COLLECTION_NAME = "document_chunks"

class VectorDBManager:
    """
    向量数据库管理器，负责向量的存储、更新和检索。
    使用 ChromaDB 作为示例。
    """
    def __init__(self, db_path: str = CHROMA_DB_PATH, collection_name: str = CHROMA_COLLECTION_NAME):
        # 使用持久化客户端
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 如果使用 OpenAI 或其他需要 API key 的嵌入函数，可以在这里配置
        # self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        # api_key="YOUR_OPENAI_API_KEY", model_name="text-embedding-ada-002"
        # )
        # 如果嵌入是在外部完成的 (如我们的 EmbeddingComponent)，则不需要 ChromaDB 的 embedding_function
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name
            # embedding_function=self.embedding_function # 如果ChromaDB负责嵌入，则需要
        )
        print(f"ChromaDB collection '{collection_name}' loaded/created at path '{db_path}'.")

    def add_chunks(self, chunks_with_embeddings: List[ChunkWithEmbedding]):
        """
        将带有嵌入的文本块添加到向量数据库。

        Args:
            chunks_with_embeddings: 带嵌入的文本块列表。
        """
        if not chunks_with_embeddings:
            return

        ids = [chunk.id for chunk in chunks_with_embeddings]
        # 将 List[List[float]] 转换为 numpy.ndarray of float32
        embeddings_list = [chunk.embedding for chunk in chunks_with_embeddings]
        if not all(isinstance(emb, list) and all(isinstance(val, float) for val in emb) for emb in embeddings_list):
            print("Warning: Some embeddings are not in List[float] format. Skipping conversion for safety.")
            # Decide on fallback or error handling if embeddings are not as expected
            # For now, we'll proceed with the original list if there's a format issue,
            # though this might not satisfy the type checker or ChromaDB.
            # A more robust solution would be to ensure embeddings are always correctly formatted upstream.
            final_embeddings = embeddings_list
        else:
            try:
                final_embeddings = np.array(embeddings_list, dtype=np.float32)
            except Exception as e:
                print(f"Error converting embeddings to numpy array: {e}. Using original list.")
                final_embeddings = embeddings_list

        documents = [chunk.text for chunk in chunks_with_embeddings]
        
        metadatas = []
        for chunk in chunks_with_embeddings:
            meta = chunk.metadata.copy() if chunk.metadata else {}
            meta["document_id"] = chunk.document_id 
            # ChromaDB 的元数据值必须是 str, int, float, or bool
            # 确保所有元数据值符合要求
            for k, v in meta.items():
                if not isinstance(v, (str, int, float, bool)):
                    meta[k] = str(v) # 转换为字符串作为后备
            metadatas.append(meta)

        try:
            self.collection.add(
                ids=ids,
                embeddings=final_embeddings.tolist() if isinstance(final_embeddings, np.ndarray) else [emb.tolist() if isinstance(emb, np.ndarray) else emb for emb in final_embeddings], # 确保嵌入向量格式符合 ChromaDB 要求
                documents=documents,
                metadatas=metadatas
            )
            print(f"Added {len(ids)} chunks to ChromaDB collection '{self.collection.name}'.")
        except Exception as e:
            print(f"Error adding chunks to ChromaDB: {e}")
            # Consider more specific error handling or re-raising

    def search_similar_chunks(self, query_embedding: List[float], top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        根据查询向量从数据库中检索相似的文本块。

        Args:
            query_embedding: 查询文本的向量嵌入。
            top_k: 返回最相似块的数量。
            filter_metadata: 用于过滤结果的元数据条件 (e.g., {"document_id": "doc_123"})

        Returns:
            一个字典列表，每个字典包含块的信息 (id, text, metadata, distance)。
        """
        if not query_embedding:
            return []

        query_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata # ChromaDB uses 'where' for metadata filtering
            # include=['metadatas', 'documents', 'distances'] # 默认包含这些
        )
        
        results = []
        if query_results and query_results.get('ids') and query_results.get('ids')[0]:
            for i in range(len(query_results['ids'][0])):
                results.append({
                    "id": query_results['ids'][0][i],
                    "text": query_results['documents'][0][i] if query_results['documents'] and query_results['documents'][0] else None,
                    "metadata": query_results['metadatas'][0][i] if query_results['metadatas'] and query_results['metadatas'][0] else None,
                    "distance": query_results['distances'][0][i] if query_results['distances'] and query_results['distances'][0] else None,
                })
        return results

    def delete_chunks_by_document_id(self, document_id: str):
        """
        删除与特定 document_id 相关的所有块。
        这在文档更新或删除时很有用。
        """
        try:
            self.collection.delete(where={"document_id": document_id})
            print(f"Deleted chunks for document_id '{document_id}' from ChromaDB.")
        except Exception as e:
            print(f"Error deleting chunks for document_id '{document_id}': {e}")

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """获取特定 ID 的块"""
        result = self.collection.get(ids=[chunk_id])
        if result and result.get('ids') and result['ids']:
            return {
                "id": result['ids'][0],
                "text": result['documents'][0] if result['documents'] else None,
                "metadata": result['metadatas'][0] if result['metadatas'] else None,
                "embedding": result['embeddings'][0] if result['embeddings'] else None,
            }
        return None

    def document_exists_in_vector_db(self, document_id: str) -> bool:
        """
        检查给定 document_id 的文档是否已存在于向量数据库中。
        通过查询是否存在任何关联到该 document_id 的块来判断。
        """
        try:
            # 尝试查询与该 document_id 关联的任何块
            # n_results=1 意味着我们只需要知道是否存在至少一个块
            results = self.collection.query(
                query_texts=[""], # 空查询文本，因为我们只关心元数据过滤
                n_results=1,
                where={"document_id": document_id},
                include=[] # 不需要返回文档、嵌入或距离，只关心是否存在
            )
            # 如果 ids 列表中有任何结果，则表示文档存在
            return bool(results and results.get('ids') and results['ids'][0])
        except Exception as e:
            print(f"Error checking document existence for {document_id}: {e}")
            return False

# TODO: 添加更新块的逻辑，可能涉及先删除再添加。
# TODO: 考虑更复杂的错误处理和日志记录。