from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from src.file_assiant import FileAssiant
from src.api.models.rule_models import RuleCreate, RuleUpdate # 确保这些模型存在或根据需要创建


# 创建 FastAPI 路由器
router = APIRouter(
    prefix="/file_assistant",
    tags=["file_assistant"],
    responses={404: {"description": "Not found"}},
)

# 依赖注入，获取 FileAssiant 实例
def get_file_assiant():
    return FileAssiant()

# 定义请求体模型
class UploadFileRequest(BaseModel):
    source_type: str
    file_path: str

class UploadTextRequest(BaseModel):
    text_content: str
    title: str

class CheckFileRequest(BaseModel):
    source_type: str
    file_path: str

class SetRuleStatusRequest(BaseModel):
    rule_name: str
    is_active: bool

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3


@router.post("/upload_file", summary="上传文件到知识库和数据库")
async def upload_file_api(request: UploadFileRequest, file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    上传文件到知识库和数据库。

    - **source_type**: 文件来源类型 [local_file, confluence]
    - **file_path**: 文件路径
    """
    result = file_assiant.upload_file(request.source_type, request.file_path)
    return {"message": result}

@router.post("/upload_text", summary="上传文字到知识库")
async def upload_text_api(request: UploadTextRequest, file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    上传文字内容到知识库。

    - **text_content**: 文字内容
    - **title**: 文字标题
    """
    result = file_assiant.upload_text(request.text_content, request.title)
    return {"message": result}

@router.post("/check_file", summary="检查文件是否符合规范")
async def check_file_api(request: CheckFileRequest, file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    检查文件是否符合规范。

    - **source_type**: 文件来源类型 [local_file, confluence]
    - **file_path**: 文件路径
    """
    result = file_assiant.check_file_type(request.source_type, request.file_path)
    return {"message": result}

@router.post("/upload_rule", summary="上传规则")
async def upload_rule_api(rule: RuleCreate, file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    上传新的规则。

    - **rule**: 规则内容 (JSON 对象)
    """
    result = file_assiant.add_rule(rule.dict())
    return {"message": result}

@router.post("/set_rule_status", summary="设置规则的激活状态")
async def set_rule_status_api(request: SetRuleStatusRequest, file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    设置规则的激活状态。

    - **rule_name**: 规则名称
    - **is_active**: 激活状态 (true/false)
    """
    result = file_assiant.set_rule_status(request.rule_name, request.is_active)
    return {"message": result}

@router.post("/build_dependency", summary="构建数据库中所有数据的依赖关系")
async def build_dependency_api(file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    构建数据库中所有数据的依赖关系。
    """
    result = file_assiant.build_all_dependency()
    return {"message": result}

@router.post("/build_vector_db", summary="构建向量数据库")
async def build_vector_db_api(file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    构建向量数据库。
    """
    result = file_assiant.vectorize_all_documents()
    return {"message": result}

@router.post("/update_vector_db", summary="更新向量数据库")
async def update_vector_db_api(file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    更新向量数据库。
    """
    result = file_assiant.update_vec_database()
    return {"message": result}

@router.post("/search", summary="从向量数据库中搜索")
async def search_api(request: SearchRequest, file_assiant: FileAssiant = Depends(get_file_assiant)):
    """
    从向量数据库中搜索。

    - **query**: 搜索关键词
    - **top_k**: 返回结果的数量 (可选，默认为3)
    """
    top_k_value = request.top_k if request.top_k is not None else 5 
    results = file_assiant.retrieve_with_dependencies(request.query, top_k_value)
    return {"results": results}

