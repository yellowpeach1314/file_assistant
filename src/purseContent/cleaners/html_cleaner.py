from typing import Any
from bs4 import BeautifulSoup
from .base_cleaner import BaseCleaner

class HTMLCleaner(BaseCleaner):
    """HTML文本清洗器"""
    
    def __init__(self):
        self.noise_tags = {
            'script', 'style', 'nav', 'header', 'footer', 
            'meta', 'link', 'aside', 'advertisement'
        }
    
    def clean(self, content: str) -> str:
        """清洗HTML文本
        
        Args:
            content: HTML格式的文本内容
            
        Returns:
            str: 清洗后的纯文本
        """
        if not isinstance(content, str):
            return ""
            
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # 移除噪音标签
        for tag in soup.find_all(self.noise_tags):
            tag.decompose()
        
        # 获取纯文本
        text = soup.get_text(separator='\n')
        
        # 清理多余的空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text