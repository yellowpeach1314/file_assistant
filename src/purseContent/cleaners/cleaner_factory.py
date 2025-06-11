from typing import Optional
from .base_cleaner import BaseCleaner
from .markdown_cleaner import MarkdownCleaner, UniversalMarkdownCleaner
from .html_cleaner import HTMLCleaner # 取消注释
from .word_cleaner import WordCleaner # 导入新的WordCleaner

class CleanerFactory:
    """清洗器工厂类"""

    def __init__(self):
        self._cleaners = {
            'md': MarkdownCleaner(),
            'markdown': MarkdownCleaner(),
            'html': HTMLCleaner(), # 取消注释
            'htm': HTMLCleaner(), # 取消注释
            'docx': WordCleaner(), # 添加WordCleaner
            # 如果需要支持旧版.doc，需要额外的库和逻辑
            # 'doc': DocCleaner(),
            'default': UniversalMarkdownCleaner(), # 添加默认清洗器
        }

    def get_cleaner(self, content_type: str) -> Optional[BaseCleaner]:
        """根据内容类型获取对应的清洗器
        
        Args:
            content_type: 内容类型（文件扩展名或MIME类型）
            
        Returns:
            BaseCleaner: 对应的清洗器实例
        """
        content_type = content_type.lower().strip('.')
        print(f"cleaner: {content_type}")
        return self._cleaners.get(content_type, self._cleaners['default'])