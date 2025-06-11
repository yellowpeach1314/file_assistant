import re
import os
from typing import Any
from .base_cleaner import BaseCleaner
from markitdown import MarkItDown

class MarkdownCleaner(BaseCleaner):
    """Markdown文本清洗器"""

    def clean(self, content: str) -> str:
        """清洗Markdown文本

        Args:
            content: Markdown格式的文本内容

        Returns:
            str: 清洗后的纯文本
        """
        print(f"Markdown cleaner >>>>>>>>>> cleaning...")
        if not isinstance(content, str):
            return ""

        # 移除代码块
        content = re.sub(r'```[\s\S]*?```', '', content)

        # 移除行内代码
        content = re.sub(r'`[^`]*`', '', content)

        # 移除链接，保留链接文本
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

        # 移除图片标记
        content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content)

        # 移除标题标记
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)

        # 移除强调标记
        content = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', content)

        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)

        # 移除空行 (修改为按行处理)
        lines = content.splitlines()
        cleaned_lines = [line for line in lines if line.strip()]
        content = "\n".join(cleaned_lines)

        return content.strip()

# 在这里添加您的新类
class UniversalMarkdownCleaner(MarkdownCleaner):
    """继承自MarkdownCleaner的新清洗器"""
    """
       用于找不到对应的清洗器时使用的默认清洗器
       先将原数据先转换成Markdown格式，再使用MarkdownCleaner清洗
    """
    def __init__(self):
        super().__init__()
        self._mdConverter = MarkItDown(enable_plugins=False)
        # 在这里添加您新类的初始化逻辑

    def clean(self, content: str) -> str:
        """
        content 表示文件的路径
        """
        convert_content = self._mdConverter.convert(content);
        # 调用父类的clean方法获取基础清洗结果
        cleaned_content = super().clean(convert_content.text_content)

        return cleaned_content