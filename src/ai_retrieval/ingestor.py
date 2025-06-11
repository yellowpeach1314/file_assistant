import os
import shutil
from typing import Dict, Any

from .models import TextChunk, ChunkWithEmbedding
from .text_chunker import TextChunkingComponent, CharacterTextSplitter
from .embedder import EmbeddingComponent # 移除 PlaceholderEmbeddingModel
from .vector_db_manager import VectorDBManager, CHROMA_DB_PATH

class DocumentIngestor:
    """
    负责接收文档数据，进行分块、嵌入，并存储到向量数据库的组件。
    """
    def __init__(self,
                 chunk_size: int = 100,
                 chunk_overlap: int = 20,
                 embedding_dimension: int = 768):
        """
        初始化文档摄取器。

        Args:
            chunk_size (int): 文本分块的大小。
            chunk_overlap (int): 文本分块的重叠大小。
            embedding_dimension (int): 嵌入模型的维度。
        """
        self.chunker = TextChunkingComponent(splitter=CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap))
        # 直接初始化 EmbeddingComponent，它会根据 EMBEDDING_MODEL_CONFIG 选择模型
        self.embedder = EmbeddingComponent()
        self.db_manager = VectorDBManager()

    def ingest_document(self, document_text: str, document_id: str, document_metadata: Dict[str, Any]):
        """
        摄取单个文档，处理并存储到向量数据库。

        Args:
            document_text (str): 文档的原始文本内容。
            document_id (str): 文档的唯一标识符。
            document_metadata (Dict[str, Any]): 文档的元数据。
        """
        print(f"\n--- Ingesting Document: {document_id} ---")

        # 步骤 1: 文本分块
        print("Step 1: Chunking document...")
        text_chunks: list[TextChunk] = self.chunker.chunk_document(
            cleaned_text=document_text,
            document_id=document_id,
            document_metadata=document_metadata
        )
        print(f"Generated {len(text_chunks)} text chunks.")

        # 步骤 2: 生成嵌入
        print("Step 2: Generating embeddings...")
        chunks_with_embeddings: list[ChunkWithEmbedding] = self.embedder.embed_chunks(text_chunks)
        print(f"Generated embeddings for {len(chunks_with_embeddings)} chunks.")

        # 步骤 3: 添加到向量数据库
        print("Step 3: Adding chunks to Vector DB...")
        self.db_manager.add_chunks(chunks_with_embeddings)
        print("Chunks added to DB successfully.")
        print(f"--- Document {document_id} Ingestion Complete ---")

# 示例用法 (与 test_retrieval.py 类似，但通过 Ingestor 类调用)
if __name__ == "__main__":
    # 清理旧的 ChromaDB 数据 (可选，用于测试)
    if os.path.exists(CHROMA_DB_PATH):
        print(f"Cleaning up old ChromaDB data at {CHROMA_DB_PATH}...")
        shutil.rmtree(CHROMA_DB_PATH)

    ingestor = DocumentIngestor()

    # 示例文档 1
    doc1_id = "doc_001"
    doc1_text = (
        "人工智能是计算机科学的一个分支，旨在创建能够执行需要人类智能的任务的机器。"
        "这包括学习、解决问题、模式识别和理解语言。"
    )
    doc1_metadata = {"source": "wiki", "category": "technology"}
    ingestor.ingest_document(doc1_text, doc1_id, doc1_metadata)

    # 示例文档 2
    doc2_id = "doc_002"
    doc2_text = (
        "机器学习是人工智能的一个子集，它使系统能够从数据中学习，而无需明确编程。"
        "常见的机器学习算法包括监督学习、无监督学习和强化学习。"
    )
    doc2_metadata = {"source": "blog", "category": "AI"}
    ingestor.ingest_document(doc2_text, doc2_id, doc2_metadata)

    # 您现在可以使用 Retriever 来检索这些文档
    from src.ai_retrieval.retriever import Retriever
    from src.ai_retrieval.embedder import EmbeddingComponent, PlaceholderEmbeddingModel

    embedder_for_retrieval = EmbeddingComponent(embedding_model=PlaceholderEmbeddingModel(dimension=768))
    db_manager_for_retrieval = VectorDBManager()
    retriever = Retriever(embedding_component=embedder_for_retrieval, vector_db_manager=db_manager_for_retrieval)

    query = "什么是机器学习？"
    print(f"\n--- Retrieving for query: '{query}' ---")
    retrieved_chunks = retriever.retrieve_relevant_chunks(query_text=query, top_k=2)

    if retrieved_chunks:
        for i, chunk_data in enumerate(retrieved_chunks):
            print(f"Result {i+1}:")
            print(f"  ID: {chunk_data.get('id')}")
            print(f"  Distance: {chunk_data.get('distance'):.4f}")
            print(f"  Metadata: {chunk_data.get('metadata')}")
            chunk_text = chunk_data.get('text')
            if chunk_text is not None:
                print(f"  Text: {chunk_text[:200]}...")
            else:
                print("  Text: [No text content available]")
            print("---")
    else:
        print("No chunks retrieved.")

    print("--- Ingestion and Retrieval Test Complete ---")