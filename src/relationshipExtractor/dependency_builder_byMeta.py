# dependency_builder_byMeta.py

import re
from sqlalchemy.orm import Session
from ..documentRepository.database_models import DocumentDependency, DocumentDB
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
import json
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

class DependencyBuilderByMeta:
    def __init__(self, db_session: Session):
        """
        初始化 DependencyBuilderByMeta。

        Args:
            db_session: SQLAlchemy 数据库会话。
        """
        self.db_session = db_session

    def build_dependencies_for_all_documents(self):
        """
        为所有文档构建并存储依赖关系。
        """
        print("====================开始为所有文档根据元数据构建依赖关系...====================")
        all_documents = self.db_session.query(DocumentDB).all()
        for document in all_documents:
            self.build_dependencies_for_document(document)

    def build_dependencies_for_document_byId(self, doc_id: str):
        document = self._load_document(doc_id)
        if not document:
            print(f"未找到文档 {doc_id}，跳过依赖构建。")
            return
        return self.build_dependencies_for_document(document)

    def build_dependencies_for_document(self, document: DocumentDB):
        """
        根据文档的元数据为指定文档构建并存储依赖关系。

        Args:
            doc_id: 待分析文档的 ID。
        """
        print(f"====================开始为文档 {document.id} 根据元数据构建依赖关系...====================")
        print(f"成功加载文档: {document.title} (ID: {document.id})")

        # 1. 从文档元数据中提取引用信息
        meta_references = self._extract_references_from_metadata(document)

        # 2. 匹配出站引用到数据库中的已有文档
        outgoing_dependencies = self._match_meta_references_to_documents(str(document.id), meta_references)

        # 3. 执行“反向检查”：识别已有文档指向 doc_id 的引用 (Incoming Dependencies)
        #    这部分可能需要更复杂的逻辑，例如基于关键词的匹配
        # incoming_dependencies = self._identify_incoming_references_by_meta(document)

        # 4. 存储识别出的依赖关系
        # all_dependencies = outgoing_dependencies + incoming_dependencies
        all_dependencies = outgoing_dependencies
        self._store_dependencies(all_dependencies)

        print(f"完成为文档 {document.id} 根据元数据构建依赖关系。")

    def _load_document(self, doc_id: str) -> DocumentDB | None:
        """
        从数据库加载指定 ID 的文档。
        """
        document = self.db_session.query(DocumentDB).filter(DocumentDB.id == doc_id).first()
        return document

    def _extract_references_from_metadata(self, document: DocumentDB) -> dict:
        """
        从文档的 document_metadata 中提取 reference 信息。
        """
        references = {
            'keywords': [],
            'urls': [],
            'citations': []
        }
        if document.document_metadata is not None and isinstance(document.document_metadata, dict):
            meta_data = document.document_metadata.get('reference', {})
            if isinstance(meta_data, dict):
                references['keywords'] = meta_data.get('keywords', [])
                references['urls'] = meta_data.get('urls', [])
                references['citations'] = meta_data.get('citations', [])
        print(f"  - 从元数据中提取到引用: {references}")
        return references

    def _match_meta_references_to_documents(self, source_doc_id: str, meta_references: dict) -> list:
        """
        将从元数据中提取的引用匹配到数据库中的已有文档。
        """
        print(f"匹配文档 {source_doc_id} 的元数据引用到已有文档...")
        dependencies = []
        query = self.db_session.query(DocumentDB)

        # 匹配 URLs
        for url in meta_references.get('urls', []):
            # 这里想找出URL中的pageId 来在数据库中匹配
            # confluence_page_id_match = re.search(r'pageId=(\d+)', url)
            # if confluence_page_id_match:
            #     confluence_id = confluence_page_id_match.group(1)
            #     target_document = query.filter(
            #         DocumentDB.source_type == 'confluence',
            #         DocumentDB.source_identifier == confluence_id
            #     ).first()
            #     if target_document and target_document.id != source_doc_id:
            #         dependencies.append((source_doc_id, target_document.id, 'meta_link_confluence'))
            #         print(f"  - 匹配元数据链接(Confluence ID): {url} -> {target_document.id}")
            # TODO: 添加其他 URL 类型的匹配逻辑
            target_document = query.filter(
                    DocumentDB.source_identifier == url
            ).first()
            if target_document is not None and bool(target_document.id != source_doc_id):
                dependencies.append((source_doc_id, target_document.id, 'reference'))
                print(f"  - 匹配元数据链接(Confluence ID): {url} -> {target_document.id}")

        # 匹配 Citations (假设 citations 可能是文档标题或 ID)
        for citation in meta_references.get('citations', []):
            # # 尝试匹配文档 ID
            # target_document_by_id = query.filter(DocumentDB.id == citation).first()
            # if target_document_by_id and target_document_by_id.id != source_doc_id:
            #     dependencies.append((source_doc_id, target_document_by_id.id, 'meta_citation_id'))
            #     print(f"  - 匹配元数据引用(ID): {citation} -> {target_document_by_id.id}")
            #     continue
            # 尝试匹配文档标题
            target_document_by_title = query.filter(DocumentDB.title == citation).first()
            if target_document_by_title is not None and bool(target_document_by_title.id != source_doc_id):
                dependencies.append((source_doc_id, target_document_by_title.id, 'reference'))
                print(f"  - 匹配元数据引用(标题): {citation} -> {target_document_by_title.id}")

        for keyword in meta_references.get('keywords', []):
        # 使用 like 进行模糊匹配，并获取所有匹配的文档
            target_documents_by_titles = query.filter(DocumentDB.title.like(f'%{keyword}%')).all()
            for target_document_by_title in target_documents_by_titles:
                if target_document_by_title is not None and bool(target_document_by_title.id != source_doc_id):
                    dependencies.append((source_doc_id, target_document_by_title.id, 'meta_keyword'))
                    print(f"  - 在标题匹配元数据关键词: {keyword} -> {target_document_by_title.id}")

            target_documents_by_keywords = query.filter(DocumentDB.document_metadata.like(f'%{keyword}%')).all()
            for target_documents_by_keyword in target_documents_by_keywords:
                if target_documents_by_keyword is not None and bool(target_documents_by_keyword.id != source_doc_id):
                    dependencies.append((source_doc_id, target_documents_by_keyword.id, 'meta_keyword'))
                    print(f"  - 匹配元数据关键词: {keyword} -> {target_documents_by_keyword.id}")

        print(f"文档 {source_doc_id} 共匹配到 {len(dependencies)} 条出站元数据依赖。")
        return dependencies

    def _identify_incoming_references_by_meta(self, document: DocumentDB) -> list:
        """
        在已有文档中查找对当前文档的引用（反向检查），主要基于关键词匹配。
        """
        print(f"执行反向检查，查找引用文档 {document.id} 的已有文档 (基于元数据关键词)...")
        dependencies = []
        target_doc_id = document.id
        target_doc_title = document.title
        target_keywords = self._extract_references_from_metadata(document).get('keywords', [])

        if not target_keywords and not bool(target_doc_title):
            print(f"  - 文档 {target_doc_id} 没有可搜索的关键词或标题，跳过反向检查。")
            return dependencies

        print(f"  - 搜索关键词: {target_keywords}, 目标标题: {target_doc_title}")

        # 扫描所有文档（除了当前文档本身）
        potential_referencing_docs = self.db_session.query(DocumentDB).filter(DocumentDB.id != target_doc_id).all()
        print(f"  - 检查 {len(potential_referencing_docs)} 个已有文档...")

        for doc_b in potential_referencing_docs:
            if doc_b.document_metadata is not None and isinstance(doc_b.document_metadata, dict):
                doc_b_meta_data = doc_b.document_metadata.get('reference', {})
                doc_b_keywords = doc_b_meta_data.get('keywords', [])
                doc_b_urls = doc_b_meta_data.get('urls', [])
                doc_b_citations = doc_b_meta_data.get('citations', [])

                found_reference = False

                # 检查 doc_b 的元数据中是否包含目标文档的 ID 或标题
                if target_doc_id in doc_b_citations:
                    dependencies.append((doc_b.id, target_doc_id, 'meta_referenced_by_citation_id'))
                    print(f"    - 文档 {doc_b.id} 的引用中包含目标 ID {target_doc_id}")
                    found_reference = True
                elif target_doc_title is not None and target_doc_title in doc_b_citations:
                    dependencies.append((doc_b.id, target_doc_id, 'meta_referenced_by_citation_title'))
                    print(f"    - 文档 {doc_b.id} 的引用中包含目标标题 '{target_doc_title}'")
                    found_reference = True

                # 检查 doc_b 的元数据中是否包含目标文档的 URL
                for url in doc_b_urls:
                    confluence_page_id_match = re.search(r'pageId=(\d+)', url)
                    if confluence_page_id_match and confluence_page_id_match.group(1) == target_doc_id:
                        dependencies.append((doc_b.id, target_doc_id, 'meta_referenced_by_url'))
                        print(f"    - 文档 {doc_b.id} 的 URL 中包含目标 ID {target_doc_id}")
                        found_reference = True
                        break

                # 检查 doc_b 的关键词是否与目标文档的关键词有重叠
                # 这是一个更宽松的匹配，可能需要根据实际需求调整阈值
                if target_keywords and doc_b_keywords:
                    common_keywords = set(target_keywords).intersection(set(doc_b_keywords))
                    if common_keywords:
                        # 避免重复添加，如果已经通过其他方式找到引用，则不再添加关键词引用
                        if not found_reference:
                            dependencies.append((doc_b.id, target_doc_id, 'meta_referenced_by_keyword_overlap'))
                            print(f"    - 文档 {doc_b.id} 与目标文档 {target_doc_id} 有关键词重叠: {common_keywords}")
                            found_reference = True

        print(f"文档 {target_doc_id} 共识别出 {len(dependencies)} 条入站元数据依赖。")
        return dependencies

    def _store_dependencies(self, dependencies: List[Dict]):
        # 按 source_id 分组依赖关系
        grouped_dependencies = defaultdict(list)
        for source_id, target_id, relation_type in dependencies:
            if target_id and source_id != target_id:
                grouped_dependencies[source_id].append(target_id)

        for source_id, target_ids in grouped_dependencies.items():
            # 将 target_ids 列表转换为 JSON 字符串
            target_ids_json = json.dumps(list(set(target_ids))) # 使用 set 去重

            # 尝试查找现有依赖关系
            existing_dependency = self.db_session.query(DocumentDependency).filter_by(
                source_document_id=source_id
            ).first()

            if existing_dependency:
                # 如果存在，则更新 target_document_ids
                existing_dependency.target_document_ids = target_ids_json # type: ignore
                existing_dependency.updated_at = datetime.utcnow() # type: ignore
            else:
                # 如果不存在，则创建新的依赖关系
                new_dependency = DocumentDependency(
                    source_document_id=source_id,
                    target_document_ids=target_ids_json # type: ignore
                )
                self.db_session.add(new_dependency)
        try:
            self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            print(f"Error storing dependencies: {e}")
            raise