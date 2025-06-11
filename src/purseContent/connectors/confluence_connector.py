import os
from typing import Optional, Dict, Any
import requests
from .base_connector import BaseConnector
from ..document_model import Document

class ConfluenceConnector(BaseConnector):
    """Confluence数据源连接器"""
    
    def __init__(self):
        super().__init__()
        self.base_url = os.getenv("CONFLUENCE_URL")
        self.username = os.getenv("CONFLUENCE_USERNAME")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        
    def get_auth(self):
        """获取认证信息"""
        return (self.username, self.api_token)
        
    def get_headers(self):
        """获取请求头"""
        return {"Accept": "application/json"}
        
    def fetch_content(self, identifier: str) -> Optional[Document]:
        """获取Confluence页面内容"""
        url = f"{self.base_url}/rest/api/content/{identifier}"
        params = {"expand": "body.atlas_doc_format"}
        
        response = requests.get(
            url,
            headers=self.get_headers(),
            auth=self.get_auth(),
            params=params
        )
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        raw_content = data.get('body', {}).get('atlas_doc_format', {}).get('value', {})
        cleaned_text = self.parse_content(raw_content)
        
        return Document(
            id=self.generate_id(identifier),
            source_type='confluence',
            source_identifier=identifier,
            title=data.get('title', ''),
            raw_content=raw_content,
            cleaned_text=cleaned_text,
            url=f"{self.base_url}/pages/viewpage.action?pageId={identifier}",
            metadata={
                'space_key': data.get('space', {}).get('key'),
                'version': data.get('version', {}).get('number'),
                'created_by': data.get('history', {}).get('createdBy', {}).get('displayName'),
                'last_modified': data.get('history', {}).get('lastUpdated', {}).get('when')
            }
        )
        
    def parse_content(self, raw_content: Dict) -> str:
        """解析ADF内容"""
        if not raw_content or not isinstance(raw_content, dict):
            return ""
            
        text = []
        
        def extract_text(node):
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    text.append(node.get('text', ''))
                elif 'content' in node and isinstance(node['content'], list):
                    for child in node['content']:
                        extract_text(child)
                        
        extract_text(raw_content)
        return '\n'.join(text)