import os
import hashlib
from pathlib import Path
from typing import Optional, Any ,Dict
from enum import Enum

from sqlalchemy import MetaData
# 导入必要工程内部模块
from ..connectors.base_connector import BaseConnector
from ..document_model import Document
from ..cleaners.cleaner_factory import CleanerFactory
from ..meta_content import extract_metadata

class ReadableFileTypes(Enum):
    MD = 'md'
    TXT = 'txt'
    HTML = 'html'

class LocalFileConnector(BaseConnector):
    """本地文件数据源连接器"""
    def __init__(self):
        super().__init__()
        self.source_identifier = None  # 添加属性初始化
        self.path = None
    
    def generate_id(self, identifier: str) -> str:
        """基于文件路径生成唯一ID"""
        path_hash = hashlib.md5(identifier.encode()).hexdigest()
        return f"local:{path_hash}"
        
    def fetch_content(self, identifier: str) -> Optional[Document]:
        """获取本地文件内容"""
        path = Path(identifier)
        if not path.exists():
            return None
        try:
            self.source_identifier = identifier  # 设置当前处理的文件标识符
            self.path = path
            file_type = path.suffix.lstrip('.')
            raw_content = None
            if file_type in [item.value for item in ReadableFileTypes]:
                with open(path, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                cleaned_text = self.parse_content(raw_content)
            else:
                # 对于docx等不可直接读取的文件，传递路径给parse_content
                cleaned_text = self.parse_content(path)
            print("begin to extract metadata")
            ref = extract_metadata(cleaned_text)
            metaData = {
                'file_type': path.suffix,
                'file_size': os.path.getsize(path),
                'last_modified': os.path.getmtime(path),
                'reference': ref
            }
            return Document(
                # id=self.generate_id(identifier),
                id='',
                source_type='local_file',
                source_identifier=str(self.path),
                title=path.name,
                raw_content=raw_content,
                cleaned_text=cleaned_text,
                metadata=metaData,
                dependencies={}
            )
        except Exception as e:
            print(f"Error reading file {identifier}: {str(e)}")
            return None
            
    def parse_content(self, raw_content: Any) -> str:
        """根据文件类型解析内容"""
        if not self.source_identifier:
            # 如果没有source_identifier，直接返回原始内容。对于docx，content是Path对象，需要特殊处理
            if isinstance(raw_content, Path):
                return str(raw_content) # 或者抛出错误，取决于期望行为
            return raw_content
            
        # 获取文件扩展名
        file_type = Path(self.source_identifier).suffix.lstrip('.')
        
        # 使用清洗器工厂获取合适的清洗器
        cleaner = CleanerFactory().get_cleaner(file_type)
        print(f"cleaner: {cleaner}")
        if cleaner:
            # 如果文件类型在可直接读取的枚举中，或者raw_content已经是字符串，直接传递给cleaner
            if file_type in [item.value for item in ReadableFileTypes] or isinstance(raw_content, str):
                return cleaner.clean(raw_content)
            # 对于docx文件，content是Path对象，直接传递给cleaner
            elif isinstance(raw_content, Path):
                return cleaner.clean(str(raw_content)) # 将Path对象转换为字符串路径
    
        # 如果没有对应的清洗器，返回原始内容
        if isinstance(raw_content, Path):
            return str(raw_content) # 对于docx，如果无清洗器，返回路径字符串
        return raw_content