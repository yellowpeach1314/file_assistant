# src/storage/database_models.py (示例文件路径)
import json
# 导入 ForeignKey
from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON, BigInteger, ForeignKey, UniqueConstraint, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 假设你已经配置了数据库连接字符串
# TODO: 将这里的 DATABASE_URL 替换为你实际的数据库连接字符串
# 使用 SQLite 数据库，数据将存储在项目根目录下的 'wiki_assistant.db' 文件中
# DATABASE_URL = "sqlite:///wiki_assistant.db"
# 使用 SQLite 数据库，数据将存储在项目根目录下的database文件夹中
# DATABASE_URL = "sqlite:///database/wiki_assistant.db"
DATABASE_URL = "sqlite:////Users/ryan/Project_w/my_pra/Python_pra/wiki_assiant/database/wiki_assistant.db"
Base = declarative_base()

class DocumentDB(Base):
    """
    数据库中的文档模型，映射到 'documents' 表
    """
    __tablename__ = 'documents'

    id = Column(String, primary_key=True) # 使用文档的唯一ID作为主键
    source_type = Column(String)
    source_identifier = Column(String)
    title = Column(String)
    raw_content = Column(Text)
    cleaned_text = Column(Text)
    document_metadata = Column(JSON) # 将 metadata 列名修改为 document_metadata
    dependencies = Column(JSON) # 使用 JSON 类型存储依赖关系
    ingestion_timestamp = Column(DateTime, default=datetime.utcnow) # 摄取时间戳
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # 更新时间戳
    is_Vectorlized = Column(Boolean, default=False) # 是否向向量数据库中添加

    def __repr__(self):
        return f"<DocumentDB(id='{self.id}', title='{self.title}')>"

class DocumentDependency(Base):
    """
    映射到 document_dependencies 表的 SQLAlchemy 模型。
    存储文档之间的依赖关系。
    """
    __tablename__ = 'document_dependencies'
    # id = Column(Integer, primary_key=True, autoincrement=True) # 表的自增主键
    source_document_id = Column(String, ForeignKey('documents.id'), nullable=False, unique=True ,primary_key=True) # 依赖文档的 ID，现在是唯一的
    target_document_ids = Column(String, nullable=False) # 被依赖文档的 ID 数组的 JSON 字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 唯一约束，避免完全相同的 (source) 依赖关系重复插入
    __table_args__ = (
    )

# 新增 RuleDB 模型
class RuleDB(Base):
    """
    数据库中的规则模型，映射到 'rules' 表
    """
    __tablename__ = 'rules'

    id = Column(Integer, primary_key=True, autoincrement=True) # 自增主键
    name = Column(String, nullable=False, unique=True) # 规则名称，唯一
    description = Column(Text) # 规则描述
    type = Column(String, nullable=False) # 规则类型 (e.g., 'keyword_check', 'structure_check')
    pattern_config = Column(JSON) # 规则的具体配置/模式，使用 JSON 类型
    severity = Column(String, nullable=False, default='INFO') # 严重程度 (INFO/WARNING/ERROR)
    is_active = Column(Boolean, default=True) # 规则是否激活
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RuleDB(id={self.id}, name='{self.name}', type='{self.type}')>"

# 数据库连接和会话创建（这部分通常在应用初始化时设置）
engine = create_engine(DATABASE_URL)
# 在应用启动时运行一次，创建表（如果不存在）
# Base.metadata.create_all(engine) 需要更新以包含新的 RuleDB 模型
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)