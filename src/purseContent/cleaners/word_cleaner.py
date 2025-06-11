from typing import Any
from docx import Document
from .base_cleaner import BaseCleaner

class WordCleaner(BaseCleaner):
    """Word (.docx) 文本清洗器"""

    def clean(self, content: Any) -> str:
        """清洗Word (.docx) 文本

        Args:
            content: Word文档的内容。这里假设content是文件路径或文件对象。

        Returns:
            str: 清洗后的纯文本
        """
        print(f"Word cleaner >>>>>>>>>> cleaning...")
        if not content:
            return ""

        try:
            # 尝试打开文档
            document = Document(content)
            text = []
            for paragraph in document.paragraphs:
                text.append(paragraph.text)
            # 使用换行符连接所有段落文本
            print(f"text: {text}")
            cleaned_text = "\n".join(text)

            # 您可以在这里添加其他清洗步骤，例如移除多余空白行等
            # 移除空行
            lines = cleaned_text.splitlines()
            cleaned_lines = [line for line in lines if line.strip()]
            cleaned_text = "\n".join(cleaned_lines)

            return cleaned_text.strip()
        except Exception as e:
            print(f"Error cleaning Word document: {e}")
            return ""