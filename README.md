# Wiki Assistant

一个强大的知识库助手，旨在从多种数据源摄取、处理、存储和检索信息。它支持文件合规性检查、文档向量化、依赖关系构建以及智能搜索功能。

## 功能特点

- **多源数据摄取**: 支持从本地文件系统和 Confluence 等多种来源获取内容。
- **文档合规性检查**: 根据预设规则检查文档内容是否符合规范。
- **智能文本处理**: 提取文本中的关键词、URL 和引用等元数据。
- **文档存储与管理**: 将处理后的文档存储到数据库中，并支持文档的更新和管理。
- **依赖关系构建**: 自动分析文档间的引用关系，构建知识图谱。
- **向量化与检索**: 将文档内容向量化，支持高效的语义搜索和相关信息检索。
- **可扩展架构**: 模块化的设计，易于集成新的数据源、清洗器、规则和检索模型。
- **API 接口**: 提供 RESTful API 接口，方便集成到其他应用中。

## 模块概览

- `src/purseContent`: 负责内容摄取、清洗和元数据提取。
  - `connectors`: 定义了不同数据源的连接器（如 `ConfluenceConnector`, `LocalFileConnector`）。
  - `cleaners`: 提供了内容清洗功能。
  - `meta_content`: 用于提取文本元数据（关键词、URL、引用）。
  - `ingestion_coordinator`: 协调不同数据源的内容摄取。
- `src/norms_checker`: 实现文档合规性检查逻辑，根据预设规则验证文档内容。
- `src/documentRepository`: 处理文档的持久化存储，包括数据库模型和存储操作。
- `src/relationshipExtractor`: 负责构建文档之间的依赖关系。
- `src/ai_retrieval`: 包含文档向量化、向量数据库管理和检索功能。
  - `embedder`: 负责生成文本嵌入向量。
  - `vector_db_manager`: 管理向量数据库的交互。
  - `ingestor`: 协调文档的向量化摄取。
  - `retriever`: 提供基于语义的文档检索功能。
- `src/api`: 定义了 FastAPI 接口，用于暴露各项功能。
  - `routers`: 包含不同功能的 API 路由（如文件上传、搜索、规则管理）。
  - `models`: 定义了 API 请求和响应的数据模型。
- `src/file_assiant.py`: 核心业务逻辑协调器，整合了上述模块的功能。
- `src/main.py`: FastAPI 应用的入口文件。

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
uvicorn src.main:app --reload
```

## API 文档

访问 `http://localhost:8000/docs` 查看交互式 API 文档 (Swagger UI)。

## 使用示例

### 上传本地文件

```bash
curl -X POST http://localhost:8000/file_assistant/upload_file \
-H "Content-Type: application/json" \
-d '{
    "source_type": "local_file",
    "file_path": "/path/to/your/document.md"
}'
```

### 上传文本内容

```bash
curl -X POST http://localhost:8000/file_assistant/upload_text \
-H "Content-Type: application/json" \
-d '{
    "text_content": "这是一段示例文本，包含关键词：AI，以及引用：[参考资料].",
    "title": "示例文本"
}'
```

### 搜索知识库

```bash
curl -X POST http://localhost:8000/file_assistant/search \
-H "Content-Type: application/json" \
-d '{
    "query": "关于AI的文档",
    "top_k": 5
}'
```