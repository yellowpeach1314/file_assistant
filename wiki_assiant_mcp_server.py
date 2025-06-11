from mcp.server.fastmcp import FastMCP
from src.file_assiant import FileAssiant
import asyncio
import os

mcp = FastMCP("wiki_assistant_mcp")

@mcp.tool()
def upload_file(source_type: str, file_path: str) -> str:
    """ Upload a file to the server

    descriptions:
        上传文件到知识库和数据库,调用此工具时请遵守Args中的参数规范。
        输入:文件来源类型(source_type:str), 文件路径(file_path:str)
        【注意path要输入完整路径,source_type要从设定的几种值中选一个】
        输出:文件检测结果报告+文件是否成功加入知识库【信息】(str)
    
    Args:
        source_type (str): 上传文件的来源类型 [local_file, confluence]
        file_path (str): 文件路径

    Returns:
        str: 文件检测结果报告+文件是否成功加入知识库【信息】
    """
    assiant = FileAssiant()
    return assiant.upload_file(source_type, file_path)

@mcp.tool(name='upload_text')
def upload_text(text_content: str ,title: str) -> str:
    """ Upload text to the server

    descriptions:
        上传文字,调用此工具时，请总结用户输入的原始内容，将总结结果作为上传文字的内容，并且总结标题，然后调用此工具。
        输入:文字内容(text_content:str), 文字标题(title:str)
        输出:文字是否成功加入知识库【信息】(str)

    Args:
        text_content (str): 文字内容.
        title (str): 文字标题.

    Returns:
        str containing the result of "文字是否成功加入知识库【信息】"
    """
    assiant = FileAssiant()
    return assiant.upload_text(text_content,title)

@mcp.tool()
def check_file(source_type: str, file_path: str) -> str:
    """Check if a file is conform to norms
    
    descriptions:
        检查文件是否符合规范。

    Args:
        source_type: 上传文件的来源类型 [local_file, confluence]
        file_path: 文件路径

    Returns:
        文件检测结果报告
    """
    assiant = FileAssiant()
    return assiant.check_file_type(source_type, file_path)

@mcp.tool()
def upload_rule(rule: dict) -> str:
    """Upload a rule to the server
    
    descriptions:
        上传规则。
        # 输入示例：
                {
                    "name": "MyNewRule",
                    "description": "This is a description for my new rule.",
                    "type": "keyword_check",
                    "pattern_config": {
                                        "keywords": [
                                        "背景",
                                        "埋点"
                                        ],
                                        "match_type": "must_include"
                                    }
                    "severity": "ERROR",
                    "is_active": true
                }
    
    Args:
        rule (dict): 规则内容
    
    Returns:
        str : 规则是否成功加入数据库【信息】
    """
    assiant = FileAssiant()
    return assiant.add_rule(rule)

@mcp.tool()
def set_rule_status(rule_name: str, is_active: bool) -> str:
    """Set the status of a rule

    descriptions:
        设置规则的激活状态。
        # 输入示例：
                {
                    "name": "MyNewRule",
                    "is_active": true
                }

    Args:
        rule_name (str): 规则名称
        is_active (bool): 激活状态

    Returns:
        str: 规则是否成功设置激活状态【信息】
    """
    assiant = FileAssiant()
    return assiant.set_rule_status(rule_name, is_active)

@mcp.tool()
def build_dependency() -> str:
    """Build dependency for all data in the database

    descriptions:
        构建数据库中所有数据的依赖关系。
    
    Args:
        None
    
    Returns:
        数据库中所有数据的依赖关系【信息】
    """
    assiant = FileAssiant()
    return assiant.build_all_dependency()

@mcp.tool()
def build_vector_db() -> str:
    """Build vector database

    descriptions:
        构建向量数据库。

    Args:
        None
    
    Returns:
        向量数据库是否成功建立【信息】
    """
    assiant = FileAssiant()
    return assiant.vectorize_all_documents()

@mcp.tool()
def update_vector_db() -> str:
    """Update vector database

    descriptions:
        更新向量数据库。

    Args:
        None

    Returns:
        向量数据库是否成功更新【信息】
    """
    assiant = FileAssiant()
    return assiant.update_vec_database()

@mcp.tool()
def search(query: str) -> list:
    """Search in the vector database

    descriptions:
        从向量数据库中搜索。

    Args:
        query (str): 搜索关键词

    Returns:
        搜索结果
    """
    assiant = FileAssiant()
    return assiant.retrieve_with_dependencies(query)

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == "sse":
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())

# 使用 SSE 传输方式运行 MCP 服务器
# 1. uv run wiki_assiant_mcp_server.py
# 2. mcp client >> json 
# {
#   "mcpServers": {
#     "****": {
#       "transport": "sse",
#       "url": "http://localhost:8000/sse"
#     }
#   }
# }