from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# 导入数据库会话依赖
from ...documentRepository.database_models import SessionLocal
# 导入文档相关的模型
from ..models.document_models import IngestRequest, IngestResponse
# 导入摄取协调器和文档存储
from ...purseContent.ingestion_coordinator import IngestionCoordinator
from ...documentRepository.document_storage import DocumentStorage
# 导入规范检查器和依赖构建器 (后续会用到)
from ...norms_checker import NormsChecker
from ...relationshipExtractor.dependency_builder import DependencyBuilder

# 创建 FastAPI 路由器
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 文档摄取端点
@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_document(request: IngestRequest, db: Session = Depends(get_db)):
    """
    根据来源类型和标识符摄取文档
    """
    ingestion_coordinator = IngestionCoordinator()
    document_storage = DocumentStorage(db)

    # 1. 使用摄取协调器获取文档内容
    document = ingestion_coordinator.ingest(request.source_type, request.source_identifier)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest document from source type '{request.source_type}' with identifier '{request.source_identifier}'"
        )

    # TODO: 3. 触发规范检查 (异步或同步)
    norms_checker = NormsChecker(db)
    # 使用 check_document_norms 方法，该方法会从数据库加载文档进行检查
    # 注意：这里需要先将文档存储到数据库才能通过 ID 进行检查
    # 如果希望在存储前检查，需要修改 NormsChecker 的接口，使其可以直接接收 Document 对象或 cleaned_text
    # 考虑到当前的 NormsChecker.check_document_norms 接收 document_id，
    # 并且文档对象 document 已经包含了 cleaned_text，
    # 我们可以直接使用 check_text_norms 方法，传入 document.cleaned_text
    check_result = norms_checker.check_text_norms(document.cleaned_text)
    print(f"Norm check result for {document.id}: {check_result.summary}")

    # 只有当规范检查通过时才存储文档并构建依赖关系
    if check_result.passed:
        # 2. 将文档存储到数据库 (upsert)
        try:
            document_storage.upsert_document(document)
            print(f"Document '{document.title}' ({document.id}) stored successfully after norm check.")
        except Exception as e:
            # 存储失败，回滚事务并抛出异常
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store document in database after norm check: {e}"
            )

        # 4. 触发依赖关系构建 (异步或同步)
        # 注意：依赖关系构建通常需要文档已经在数据库中，以便进行反向查找
        # 因此将其放在存储之后是合理的
        dependency_builder = DependencyBuilder(db)
        # 依赖构建器需要文档 ID
        dependency_builder.build_dependencies_for_document(document.id)
        print(f"Dependency building triggered for {document.id}")

        return IngestResponse(
            document_id=document.id,
            message=f"Document '{document.title}' ({document.id}) ingested, stored, and dependencies built successfully after passing norm check."
        )
    else:
        # 如果规范检查未通过，返回相应的错误响应
        # 可以选择不存储文档，或者存储文档但标记其状态为“未通过检查”
        # 这里选择不存储，并返回错误信息
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document '{document.title}' ({document.id}) failed norm check. Summary: {check_result.summary}"
        )

# TODO: 添加其他端点，例如：
# - GET /documents/{document_id} - 获取文档详情
# - GET /documents/ - 列出所有文档
# - POST /documents/{document_id}/check - 手动触发规范检查
# - POST /documents/{document_id}/build_dependencies - 手动触发依赖构建
# - GET /documents/{document_id}/violations - 获取文档的规范违规列表
# - GET /documents/{document_id}/dependencies - 获取文档的依赖关系图