# 功能：提取文本中的元数据
# 输入：文本（str）
# 输出：元数据（dict）
# 功能1: 找出文本中的关键词 【关键词可能会在文本中多次提及/但是关键词通常不是动词或者代词】
# 功能2: 找出文本中的URL 【文本中可能会引用其他的链接】
# 功能3: 找出文本中的引用 【文本中可能文字的方式提要该文本与其他的文件资料直接的关联】

import re
import spacy
from collections import Counter

# --- 环境设置 ---
# 确保你已经运行了:
# pip install spacy
# python -m spacy download zh_core_web_sm
# -----------------

# 在程序开始时加载模型，以提高效率
try:
    nlp = spacy.load("zh_core_web_sm")
except OSError:
    print("错误：找不到spaCy中文模型 'zh_core_web_sm'。")
    print("请运行: python -m spacy download zh_core_web_sm")
    nlp = None

# --- 功能函数定义 ---

def find_keywords(text: str, top_n: int = 5) -> list:
    """功能1: 提取关键词"""
    if not nlp:
        return ["spaCy模型未加载"]
    doc = nlp(text)
    keywords = [
        token.text for token in doc 
        if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and not token.is_punct
    ]
    return [word for word, freq in Counter(keywords).most_common(top_n)]

def find_urls(text: str) -> list:
    """功能2: 提取URL"""
    url_pattern = r'https?://[a-zA-Z0-9_./?=&-]*'
    return re.findall(url_pattern, text)

def find_citations(text: str) -> list:
    """功能3: 提取引用"""
    # 引用模式列表，可以轻松扩展
    patterns = [
        r"(?:参考|出自)：《(.*?)》",  # 参考：《XXX》
        r"来源：(\S+)",             # 来源：XXX
        r"引用于“(.*?)”"             # 引用于“XXX”
    ]
    citations = []
    for pattern in patterns:
        citations.extend(re.findall(pattern, text))
    return list(set(citations)) # 去重

# --- 主函数 ---

def extract_metadata(text: str) -> dict:
    """
    从输入文本中提取元数据。
    
    :param text: (str) 输入的文本。
    :return: (dict) 包含关键词、URL和引用的元数据字典。
    """
    keywords = find_keywords(text)
    urls = find_urls(text)
    citations = find_citations(text)

    return {
        'keywords': keywords,
        'urls': urls,
        'citations': citations
    }
