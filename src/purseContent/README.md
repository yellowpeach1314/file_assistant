# Confluence API 交互工具

这个工具提供了与 Confluence Cloud API 交互的功能，可以用于获取、搜索和处理 Confluence 页面内容。

## 功能特点

- 安全的 API 认证（使用环境变量存储凭据）
- 获取特定页面内容（支持 ADF 和 Storage 格式）
- 使用 CQL (Confluence Query Language) 搜索页面
- 自动处理分页获取所有匹配结果
- 解析 ADF (Atlas Document Format) 内容
- 完善的错误处理和重试机制

## 环境设置

1. 复制 `.env.example` 文件为 `.env`：
   ```
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填入你的 Confluence 凭据：
   ```
   CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
   CONFLUENCE_USERNAME=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token-here
   ```

   > 注意：API Token 可以在 [Atlassian 账号设置](https://id.atlassian.com/manage-profile/security/api-tokens) 中生成。

## 使用方法

### 获取特定页面内容

```python
from purseContent import get_page_content

page_id = "123456789"  # 替换为实际的页面ID
page_data = get_page_content(page_id)

if page_data:
    print(f"页面标题: {page_data['title']}")
```

### 搜索页面

```python
from purseContent import search_pages

# 基本搜索
results = search_pages(query="项目文档")

# 在特定空间中搜索
results = search_pages(query="项目文档", space_key="DEV")

# 搜索带有特定标签的页面
results = search_pages(label="important")
```

### 获取所有匹配页面（自动处理分页）

```python
from purseContent import get_all_pages

# 获取特定空间中的所有页面
all_pages = get_all_pages(space_key="DEV")
print(f"总共找到 {len(all_pages)} 个页面")
```

### 解析 ADF 内容

```python
from purseContent import get_page_content, parse_adf_content
import json

page_id = "123456789"  # 替换为实际的页面ID
page_data = get_page_content(page_id)

if page_data and 'body' in page_data and 'atlas_doc_format' in page_data['body']:
    adf_content = page_data['body']['atlas_doc_format']['value']
    # 可能是JSON字符串或已解析的字典
    if isinstance(adf_content, str):
        adf_content = json.loads(adf_content)
    
    text_content = parse_adf_content(adf_content)
    print(f"页面内容: {text_content}")
```

## 错误处理

该工具实现了完善的错误处理机制，包括：

- 认证失败 (401)
- 权限不足 (403)
- 资源未找到 (404)
- 请求频率限制 (429，包含自动重试)
- 其他API错误

## 注意事项

- 请确保安全存储和使用 API Token，不要将其硬编码在代码中或提交到版本控制系统
- 对于大型 Confluence 实例，请注意 API 调用频率限制
- ADF 解析功能提供了基本实现，复杂内容（如表格、列表等）可能需要更复杂的解析逻辑