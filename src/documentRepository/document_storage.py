# src/storage/document_storage.py (示例文件路径)
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert # 导入 PostgreSQL 的 ON CONFLICT 语法
from ..purseContent.document_model import Document # 导入标准文档模型
from .database_models import DocumentDB, SessionLocal # 导入数据库模型和会话工厂
from datetime import datetime

class DocumentStorage:
    """
    负责将标准文档对象存储到数据库
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def generate_id(self, identifier: str) -> str:
        """基于文件路径生成唯一ID"""
        path_hash = hashlib.md5(identifier.encode()).hexdigest()
        return f"local:{path_hash}"

    def upsert_document(self, document: Document):
        """
        插入或更新一个文档记录
        """
        document.id = self.generate_id(document.source_identifier)
        print(f"=========================== start upsert_document: {document.id} ===========================")
        try:
            # 方式 B: 使用 ON CONFLICT (PostgreSQL 特有，效率高)
            # 构建插入语句
            insert_stmt = insert(DocumentDB).values(
                id=document.id,
                source_type=document.source_type,
                source_identifier=document.source_identifier,
                title=document.title,
                raw_content=document.raw_content,
                cleaned_text=document.cleaned_text,
                document_metadata=document.metadata, # SQLAlchemy 会自动处理 Python dict 到 JSON
                dependencies=document.dependencies,
                ingestion_timestamp=datetime.utcnow(), # 插入时记录当前时间
                updated_date=datetime.utcnow() # 插入和更新时都记录当前时间
            )

            # 定义冲突时更新的字段
            on_conflict_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['id'], # 指定冲突发生的列
                set_=dict(
                    source_type=insert_stmt.excluded.source_type,
                    source_identifier=insert_stmt.excluded.source_identifier,
                    title=insert_stmt.excluded.title,
                    raw_content=insert_stmt.excluded.raw_content,
                    cleaned_text=insert_stmt.excluded.cleaned_text,
                    document_metadata=insert_stmt.excluded.document_metadata,
                    dependencies=insert_stmt.excluded.dependencies,
                    updated_date=datetime.utcnow() # 冲突时更新时间戳
                    # ingestion_timestamp 不更新，因为它记录的是首次摄取时间
                )
            )

            # 执行语句
            self.db_session.execute(on_conflict_stmt)
            self.db_session.commit()
            print(f"Successfully upserted document: {document.id}")

        except Exception as e:
            self.db_session.rollback() # 发生错误时回滚事务
            print(f"Error upserting document {document.id}: {str(e)}")
            # 这里可以添加更详细的日志记录或错误处理逻辑

    # 方式 A: 查询后判断 (ORM 方式) - 备选，如果不用 ON CONFLICT
    # def upsert_document_orm(self, document: Document):
    #     existing_doc = self.db_session.query(DocumentDB).filter_by(id=document.id).first()
    #
    #     if existing_doc:
    #         # 更新现有文档
    #         existing_doc.source_type = document.source_type
    #         existing_doc.source_identifier = document.source_identifier
    #         existing_doc.title = document.title
    #         existing_doc.raw_content = document.raw_content
    #         existing_doc.cleaned_text = document.cleaned_text
    #         existing_doc.metadata = document.metadata
    #         existing_doc.dependencies = document.dependencies
    #         existing_doc.updated_date = datetime.utcnow()
    #         # ingestion_timestamp 不更新
    #         print(f"Updating document: {document.id}")
    #     else:
    #         # 插入新文档
    #         new_doc = DocumentDB(
    #             id=document.id,
    #             source_type=document.source_type,
    #             source_identifier=document.source_identifier,
    #             title=document.title,
    #             raw_content=document.raw_content,
    #             cleaned_text=document.cleaned_text,
    #             metadata=document.metadata,
    #             dependencies=document.dependencies,
    #             ingestion_timestamp=datetime.utcnow(),
    #             updated_date=datetime.utcnow()
    #         )
    #         self.db_session.add(new_doc)
    #         print(f"Inserting document: {document.id}")
    #
    #     try:
    #         self.db_session.commit()
    #         print(f"Successfully committed document: {document.id}")
    #     except Exception as e:
    #         self.db_session.rollback()
    #         print(f"Error committing document {document.id}: {str(e)}")


    # 方式 C: 使用 session.merge() (ORM 方式，更简洁) - 备选
    # def upsert_document_merge(self, document: Document):
    #     # 创建一个临时的 DocumentDB 对象
    #     doc_to_merge = DocumentDB(
    #         id=document.id,
    #         source_type=document.source_type,
    #         source_identifier=document.source_identifier,
    #         title=document.title,
    #         raw_content=document.raw_content,
    #         cleaned_text=document.cleaned_text,
    #         metadata=document.metadata,
    #         dependencies=document.dependencies,
    #         # merge() 会根据主键查找，如果找到则更新，找不到则插入
    #         # 对于更新，它会合并字段。需要注意 ingestion_timestamp 的处理
    #         # 可能需要在 merge 之前或之后单独处理 ingestion_timestamp
    #         ingestion_timestamp=datetime.utcnow(), # 这里的逻辑需要根据 merge 的具体行为调整
    #         updated_date=datetime.utcnow()
    #     )
    #
    #     try:
    #         merged_doc = self.db_session.merge(doc_to_merge)
    #         self.db_session.commit()
    #         print(f"Successfully merged document: {document.id}")
    #     except Exception as e:
    #         self.db_session.rollback()
    #         print(f"Error merging document {document.id}: {str(e)}")

    def close_session(self):
        """关闭数据库会话"""
        self.db_session.close()

# # 假设你已经获取了一个 Document 对象
# sample_document = Document()

# # 获取数据库会话
# db_session = SessionLocal()

# # 创建存储实例
# storage = DocumentStorage(db_session)

# # 存储文档
# storage.upsert_document(sample_document)

# # 关闭会话
# storage.close_session()