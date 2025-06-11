from pydantic import BaseModel
from typing import Optional, Dict, Any

class IngestRequest(BaseModel):
    """
    文档摄取请求体模型
    """
    source_type: str # 数据来源类型 (e.g., 'confluence', 'local_file')
    source_identifier: str # 原始标识符 (e.g., Confluence page ID, file path)
    # 可以根据需要添加其他字段，例如 metadata, specific_options 等

class IngestResponse(BaseModel):
    """
    文档摄取响应模型
    """
    document_id: str # 成功摄取文档的内部 ID
    message: str # 状态消息
    # 可以添加其他字段，例如是否触发了后续处理 (检查、构建依赖)

# TODO: 添加其他文档相关的模型，例如 DocumentDetail, DocumentList, DependencyGraph 等