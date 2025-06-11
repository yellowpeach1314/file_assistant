# server.py
from typing import Optional
from mcp.server.fastmcp import FastMCP
import asyncio
from ...purseContent.ingestion_coordinator import IngestionCoordinator
from ...documentRepository.document_storage import DocumentStorage
# 导入数据库会话依赖
from ...documentRepository.database_models import SessionLocal


# Create an MCP server
mcp = FastMCP("Demo")
# Add this project core function
# 依赖项：获取数据库会话
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# 上传本地文件 输入：文件路径 输出：文件检测结果报告+文件成功加入知识库【信息】
@mcp.tool("description" == "Upload a file to the server")
def upload_file(file_path: str) -> str:
    """Upload a file to the server"""
    ingestion_coordinator = IngestionCoordinator()
    # document_storage = DocumentStorage(db)
        # 1. 使用摄取协调器获取文档内容
    document = ingestion_coordinator.ingest("local_file", file_path)
    if document:
        print(f"Document ingested successfully: {document.id}")
    else:
        print(f"Failed to ingest document from {file_path}")
    return f"Uploaded file: {document.cleaned_text}"

# 检测文件格式 输入：文件路径 输出：文件格式检测结果+文件格式【信息】
@mcp.tool("description" == "Detect the format of a file")
def detect_file_format(file_path: str) -> str:
    """Detect the format of a file"""
    return f"Detected file format: {file_path}"

# 查询rag数据
@mcp.tool("description" == "Query the RAG data")
def query_rag_data(query: str) -> str:
    """Query the RAG data"""
    return f"Query: {query}"

# test
@mcp.tool("description" == "Test")
def test() -> str:
    """Test"""
    return f"Test"

if __name__ == "__main__":  
    mcp.run()

    