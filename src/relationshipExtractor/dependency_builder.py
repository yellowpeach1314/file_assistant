# dependency_builder.py

import re # 导入正则表达式模块
from sqlalchemy.orm import Session
# 导入正确的 SQLAlchemy 模型 DocumentDB
from ..documentRepository.database_models import DocumentDependency, DocumentDB
from sqlalchemy import or_ # 导入 or_ 用于构建 OR 条件
from sqlalchemy import text # 导入 text 用于执行原生 SQL 或构建文本表达式
from sqlalchemy.exc import IntegrityError # 导入 IntegrityError 处理唯一约束冲突

class DependencyBuilder:
    def __init__(self, db_session: Session):
        """
        初始化 DependencyBuilder。

        Args:
            db_session: SQLAlchemy 数据库会话。
        """
        self.db_session = db_session

    def build_dependencies_for_document(self, doc_id: str):
        """
        为指定文档构建并存储依赖关系。

        Args:
            doc_id: 待分析文档的 ID。
        """
        print(f"====================开始为文档 {doc_id} 构建依赖关系...====================")

        # 步骤 2: 加载待分析文档
        document = self._load_document(doc_id)
        if not document:
            print(f"未找到文档 {doc_id}，跳过依赖构建。")
            return

        print(f"成功加载文档: {document.title} (ID: {document.id})")

        # TODO: 实现步骤 3-6
        # 步骤 3: 识别从 doc_id 指向其他文档的潜在引用 (Outgoing Dependencies)
        outgoing_references = self._identify_outgoing_references(document)

        # 步骤 4: 匹配潜在引用到数据库中的已有文档
        # 显式将 document.id 转换为 str 类型以满足类型检查器
        outgoing_dependencies = self._match_references_to_documents(str(document.id), outgoing_references)

        # 步骤 5: 执行“反向检查”：识别已有文档指向 doc_id 的引用 (Incoming Dependencies)
        incoming_dependencies = self._identify_incoming_references(document)

        # 步骤 6: 存储识别出的依赖关系
        all_dependencies = outgoing_dependencies + incoming_dependencies
        self._store_dependencies(all_dependencies)

        print(f"完成为文档 {doc_id} 构建依赖关系。")


    def _load_document(self, doc_id: str) -> DocumentDB | None: # 修改返回类型提示为 DocumentDB
        """
        从数据库加载指定 ID 的文档。

        Args:
            doc_id: 文档 ID。

        Returns:
            DocumentDB 对象或 None。
        """
        # 使用 SQLAlchemy 查询 documents 表，使用 DocumentDB 模型
        document = self.db_session.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
        return document

    def _identify_outgoing_references(self, document: DocumentDB) -> list: # 修改参数类型提示为 DocumentDB
        """
        识别文档内容中的出站引用（链接、ID、标题提及等）。

        Args:
            document: 待分析的 DocumentDB 对象。

        Returns:
            一个列表，包含识别出的潜在引用，格式为 (引用值, 引用类型)。
            引用类型可以是 'link_url', 'mention_id', 'mention_title' 等。
        """
        print(f"识别文档 {document.id} 的出站引用...")
        references = []

        # 1. 检查 document.document_metadata 中是否包含已提取的链接信息
        # 假设 document_metadata 是一个字典，并且可能包含一个键 'extracted_links'，其值是一个链接列表
        if document.document_metadata is not None and isinstance(document.document_metadata, dict):
            extracted_links = document.document_metadata.get('reference')
            if isinstance(extracted_links, list):
                for link in extracted_links:
                    # 假设每个 link 是一个字典，包含 'url' 键
                    if isinstance(link, dict) and 'url' in link:
                        references.append((link['url'], 'link_url'))
                        print(f"  - 发现元数据链接: {link['url']}")

        # 2. 扫描 document.cleaned_text 进行模式匹配
        if document.cleaned_text is not None:
            text = document.cleaned_text

            # 示例：匹配简单的 URL 模式 (http/https链接)
            url_pattern = re.compile(r'https?://\S+')
            found_urls = url_pattern.findall(str(text))
            for url in found_urls:
                # 避免重复添加已经在 metadata 中找到的链接
                if (url, 'link_url') not in references:
                     references.append((url, 'link_url'))
                     print(f"  - 发现文本URL: {url}")

            # 示例：匹配文档 ID 模式 (例如 PRD-123, SPEC-ABC-456)
            # 你需要根据实际使用的文档 ID 格式调整这个正则表达式
            # 这里的示例匹配 "WORD-数字" 或 "WORD-WORD-数字"
            id_pattern = re.compile(r'\b[A-Z]+-\d+\b|\b[A-Z]+-[A-Z]+-\d+\b')
            found_ids = id_pattern.findall(str(text))
            for doc_id_match in found_ids:
                 references.append((doc_id_match, 'mention_id'))
                 print(f"  - 发现文本ID: {doc_id_match}")

            # 示例：简单的标题提及模式 (这部分比较复杂，先留作基础示例)
            # 查找在引号或特定短语后的文本，这需要更复杂的NLP或更精确的模式
            # 这里只是一个非常简化的占位符，实际应用中需要更智能的方法
            # 例如，查找被双引号括起来的文本
            title_pattern_simple = re.compile(r'"([^"]+)"')
            found_titles = title_pattern_simple.findall(str(text))
            for title_match in found_titles:
                 # 简单的过滤，避免匹配到太短或看起来不像标题的文本
                 if len(title_match) > 5 and ' ' in title_match:
                     references.append((title_match, 'mention_title_potential'))
                     print(f"  - 发现潜在标题提及: {title_match}")

        print(f"文档 {document.id} 共识别出 {len(references)} 个潜在引用。")
        return references

    def _match_references_to_documents(self, source_doc_id: str, references: list) -> list:
        """
        将识别出的引用匹配到数据库中的已有文档。

        Args:
            source_doc_id: 来源文档的 ID。
            references: 识别出的潜在引用列表，格式为 (引用值, 引用类型)。

        Returns:
            一个列表，包含已成功匹配的依赖关系元组 (source_doc_id, target_doc_id, relation_type)。
        """
        print(f"匹配文档 {source_doc_id} 的出站引用到已有文档...")
        dependencies = []

        for ref_value, ref_type in references:
            target_document = None
            relation_type = None

            # 根据引用类型构建查询
            # 使用 DocumentDB 模型进行查询
            query = self.db_session.query(DocumentDB)

            if ref_type == 'link_url':
                # 尝试匹配 URL 到 source_identifier (例如 Confluence ID) 或一个假设的 url 字段
                # 注意：这里需要根据你的实际 documents 表结构和数据来调整匹配逻辑
                # 例如，如果 Confluence URL 包含页面 ID，可以解析 URL 提取 ID 进行匹配
                # 简单的示例：直接匹配 source_identifier 或 title (不推荐，仅为示例)
                # 更实际的做法是解析 URL，提取关键标识符进行匹配
                # 假设 Confluence URL 包含 /pages/viewpage.action?pageId=123456789
                confluence_page_id_match = re.search(r'pageId=(\d+)', ref_value)
                if confluence_page_id_match:
                    confluence_id = confluence_page_id_match.group(1)
                    # 匹配 source_type='confluence' 且 source_identifier 为提取的 ID
                    # 将 Document 替换为 DocumentDB
                    target_document = query.filter(
                        DocumentDB.source_type == 'confluence',
                        DocumentDB.source_identifier == confluence_id
                    ).first()
                    if target_document:
                         relation_type = 'link_confluence'
                         print(f"  - 匹配链接(Confluence ID): {ref_value} -> {target_document.id}")
                else:
                    # 如果不是 Confluence URL，尝试匹配其他可能的 URL 字段或逻辑
                    # 这里可以添加匹配其他 source_type 的逻辑
                    # 暂时不处理其他复杂 URL 匹配
                    pass # TODO: Add logic for other URL types if needed


            elif ref_type == 'mention_id':
                # 匹配文档 ID 提及，尝试匹配 documents.id 或 documents.source_identifier
                # 使用 DocumentDB 的属性
                target_document = query.filter(
                    or_(
                        DocumentDB.id == ref_value,
                        DocumentDB.source_identifier == ref_value
                    )
                ).first()
                if target_document:
                    relation_type = 'mention_id'
                    print(f"  - 匹配ID提及: {ref_value} -> {target_document.id}")


            elif ref_type == 'mention_title_potential':
                # 匹配潜在的标题提及，尝试精确匹配 documents.title
                # 注意：标题匹配容易出现歧义，这里只做精确匹配
                # 使用 DocumentDB 的属性
                target_document = query.filter(DocumentDB.title == ref_value).first()
                if target_document:
                    relation_type = 'mention_title'
                    print(f"  - 匹配标题提及: {ref_value} -> {target_document.id}")
                # TODO: 处理标题模糊匹配和歧义的情况


            # 如果找到匹配的文档且不是来源文档本身
            # 明确检查 relation_type 是否不是 None，以满足类型检查器
            if target_document is not None and bool(target_document.id != source_doc_id) and relation_type is not None:
                dependencies.append((source_doc_id, target_document.id, relation_type))
            elif target_document is not None and bool(target_document.id == source_doc_id):
                 print(f"  - 引用 {ref_value} 指向自身文档 {source_doc_id}，跳过。")
            else:
                 print(f"  - 未能匹配引用 {ref_value} (类型: {ref_type}) 到已有文档。")


        print(f"文档 {source_doc_id} 共匹配到 {len(dependencies)} 条出站依赖。")
        return dependencies

    def _identify_incoming_references(self, document: DocumentDB) -> list: # 修改参数类型提示为 DocumentDB
        """
        在已有文档中查找对当前文档的引用（反向检查）。

        Args:
            document: 待分析的 DocumentDB 对象（新文档）。

        Returns:
            一个列表，包含识别出的入站依赖关系元组 (source_doc_id, target_doc_id, relation_type)。
        """
        print(f"执行反向检查，查找引用文档 {document.id} 的已有文档...")
        dependencies = []

        # 获取当前文档的 ID 和标题，用于在其他文档中搜索
        target_doc_id = document.id
        target_doc_title = document.title

        # 确定搜索关键词
        search_terms = [target_doc_id]
        if target_doc_title is not None and len(str(target_doc_title)) > 3: # 避免搜索过短或空的标题
             search_terms.append(target_doc_title)

        if not search_terms:
             print(f"  - 文档 {target_doc_id} 没有可搜索的 ID 或标题，跳过反向检查。")
             return dependencies

        print(f"  - 搜索关键词: {search_terms}")

        # 步骤 5a: 选择检查范围
        # 基础版本：扫描所有文档（除了当前文档本身）
        # TODO: 优化：限制检查范围，例如只检查最近更新的文档，或同源/同空间文档
        # query = self.db_session.query(DocumentDB).filter(DocumentDB.id != target_doc_id).limit(1000) # 示例：限制1000条
        # 使用 DocumentDB 模型进行查询
        query = self.db_session.query(DocumentDB).filter(DocumentDB.id != target_doc_id) # 扫描所有文档

        # 步骤 5b: 扫描已有文档内容，查找新文档的标识符
        # 注意：直接在 cleaned_text 上使用 LIKE 或字符串查找对于大量数据效率很低
        # 强烈建议使用全文搜索索引 (如 PostgreSQL 的 full-text search, Elasticsearch 等)
        # 这里的实现是一个简单的文本包含检查示例

        # 构建搜索条件 (使用 ORM 的 filter 或原生 SQL)
        # ORM 示例 (可能效率不高):
        # search_conditions = []
        # for term in search_terms:
        #     # 使用 ilike 进行不区分大小写的模糊匹配，使用 DocumentDB 的 cleaned_text 属性
        #     search_conditions.append(DocumentDB.cleaned_text.ilike(f'%{term}%'))
        # if search_conditions:
        #     query = query.filter(or_(*search_conditions))

        # 原生 SQL 示例 (可能更灵活，取决于数据库支持的全文搜索功能)
        # 假设使用 PostgreSQL 的 plainto_tsquery 和 @@ 操作符
        # search_query_text = " | ".join([f"'{term}'" for term in search_terms]) # 示例：'ID' | '标题'
        # query = query.filter(
        #     text("to_tsvector('english', cleaned_text) @@ plainto_tsquery('english', :search_terms)").bindparams(search_terms=" ".join(search_terms))
        # )
        # TODO: 根据实际数据库类型和是否使用全文搜索来选择或实现查询方式

        # 简化实现：直接在 Python 中加载文本并查找 (非常低效，仅为演示概念)
        # 实际应用中应避免这种方式，而是在数据库层面完成搜索
        potential_referencing_docs = query.all()
        print(f"  - 检查 {len(potential_referencing_docs)} 个已有文档...")

        for doc_b in potential_referencing_docs:
            if doc_b.cleaned_text is not None:
                found_reference = False
                relation_type = None

                # 检查是否包含目标文档的 ID
                if target_doc_id in doc_b.cleaned_text:
                    dependencies.append((doc_b.id, target_doc_id, 'referenced_by_id'))
                    print(f"    - 文档 {doc_b.id} 引用了 ID {target_doc_id}")
                    found_reference = True

                # 检查是否包含目标文档的标题 (如果标题存在且未通过 ID 找到)
                # 避免重复添加依赖，如果已经通过ID找到，就不再通过标题添加同源依赖
                if target_doc_title is not None and target_doc_title in doc_b.cleaned_text and not found_reference:
                     dependencies.append((doc_b.id, target_doc_id, 'referenced_by_title'))
                     print(f"    - 文档 {doc_b.id} 引用了标题 '{target_doc_title}'")
                     found_reference = True

                # TODO: 可以添加更复杂的匹配逻辑，例如正则表达式，或者查找特定格式的引用


        print(f"文档 {target_doc_id} 共识别出 {len(dependencies)} 条入站依赖。")
        return dependencies

    def _store_dependencies(self, dependencies: list):
        """
        将识别出的依赖关系存储到 document_dependencies 表。

        Args:
            dependencies: 识别出的依赖关系列表，格式为 (source_doc_id, target_doc_id, relation_type)。
        """
        print(f"存储识别出的 {len(dependencies)} 条依赖关系...")

        new_dependency_objects = []
        for source_id, target_id, relation_type in dependencies:
            # 创建 DocumentDependency 对象
            new_dependency = DocumentDependency(
                source_document_id=source_id,
                target_document_id=target_id,
                relation_type=relation_type
            )
            new_dependency_objects.append(new_dependency)

        if not new_dependency_objects:
            print("  - 没有新的依赖关系需要存储。")
            return

        try:
            # 批量添加对象到会话
            self.db_session.add_all(new_dependency_objects)
            # 提交会话，数据库的唯一约束会自动处理重复项，并抛出 IntegrityError
            self.db_session.commit()
            print(f"  - 成功存储 {len(new_dependency_objects)} 条依赖关系。")

        except IntegrityError:
            # 如果发生 IntegrityError，说明尝试插入了重复的依赖关系
            # 在这里可以选择回滚并处理，或者使用数据库特定的 ON CONFLICT DO NOTHING
            # 对于简单的批量插入，回滚是常见的处理方式，然后可以考虑逐条插入或使用更高级的批量操作
            # 简单的处理：回滚并打印警告
            self.db_session.rollback()
            print("  - 存储依赖关系时发生唯一约束冲突，部分或全部依赖关系可能已存在。")
            # TODO: 对于生产环境，考虑更优雅的重复处理方式，例如 ON CONFLICT DO NOTHING
            # 或者在插入前先查询是否存在，但这会降低批量插入的效率。

        except Exception as e:
            # 处理其他可能的数据库错误
            self.db_session.rollback()
            print(f"  - 存储依赖关系时发生错误: {e}")
            raise # 重新抛出异常以便上层调用者处理

# 假设你的 models.py 文件中有如下 SQLAlchemy 模型定义
# 你需要根据你的实际情况调整
# ```python:models.py
# from sqlalchemy import create_engine, Column, String, Text, JSON, DateTime, ForeignKey
# from sqlalchemy.orm import sessionmaker, declarative_base
# from datetime import datetime
#
# Base = declarative_base()
#
# class Document(Base):
#     __tablename__ = 'documents'
#     id = Column(String, primary_key=True)
#     title = Column(String)
#     source_type = Column(String)
#     source_identifier = Column(String)
#     cleaned_text = Column(Text)
#     metadata = Column(JSON) # 或者 JSONB for PostgreSQL
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow)
#
# class DocumentDependency(Base):
#     __tablename__ = 'document_dependencies'
#     id = Column(Integer, primary_key=True) # 或者 String, UUID
#     source_document_id = Column(String, ForeignKey('documents.id'), nullable=False)
#     target_document_id = Column(String, ForeignKey('documents.id'), nullable=False)
#     relation_type = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow)
#
#     __table_args__ = (
#         UniqueConstraint('source_document_id', 'target_document_id', 'relation_type', name='_source_target_type_uc'),
#     )
#
# # 示例用法 (在你的数据摄取模块中)
# # from sqlalchemy import create_engine
# # from sqlalchemy.orm import sessionmaker
# # from .models import Base, Document
# # from .dependency_builder import DependencyBuilder
#
# # engine = create_engine('your_database_url')
# # Base.metadata.create_all(engine) # 如果表不存在则创建
# # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
# # def process_new_document(doc_data):
# #     db = SessionLocal()
# #     try:
# #         # 假设 doc_data 包含文档信息
# #         new_doc = Document(**doc_data)
# #         db.add(new_doc)
# #         db.commit()
# #         db.refresh(new_doc)
#
# #         # 调用 DependencyBuilder
# #         dependency_builder = DependencyBuilder(db)
# #         dependency_builder.build_dependencies_for_document(new_doc.id)
#
# #     except Exception as e:
# #         db.rollback()
# #         print(f"处理文档失败: {e}")
# #     finally:
# #         db.close()
# ```