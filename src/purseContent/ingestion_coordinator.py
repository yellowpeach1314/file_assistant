# ingestion_coordinator.py 读取文件的管理类
# user： ryan

# 导入必要的库
from typing import Optional, Dict, Type
# 导入必要工程内部模块
from .document_model import Document
from .connectors.base_connector import BaseConnector
from .connectors.confluence_connector import ConfluenceConnector
from .connectors.local_file_connector import LocalFileConnector
from ..norms_checker import NormsChecker
from ..documentRepository.database_models import SessionLocal
from ..documentRepository.document_storage import DocumentStorage

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class IngestionCoordinator:
    """摄取协调器"""
    def __init__(self):
        self._connectors: Dict[str, Type[BaseConnector]] = {
            'confluence': ConfluenceConnector,
            'local_file': LocalFileConnector,
            'default': LocalFileConnector  # 添加默认连接器
        }
    def register_connector(self, source_type: str, connector_class: Type[BaseConnector]):
        """注册新的连接器"""
        self._connectors[source_type] = connector_class
    # 只读取并清洗数据    
    def ingest(self, source_type: str, source_identifier: str) -> Optional[Document]:
        """执行数据摄取"""
        connector_class = self._connectors.get(source_type, self._connectors['default'])
        connector = connector_class()
        return connector.fetch_content(source_identifier)
