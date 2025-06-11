# file_assiant.py 文件管理类 
# 负责：文件的检查/文件的上传/文件的批量上传
# user： ryan

# 导入必要的库
import os

from numpy import emath

# 导入必要工程内部模块
from .purseContent.ingestion_coordinator import IngestionCoordinator
from .purseContent.document_model import Document # 确保 Document 模型被导入
from .purseContent.meta_content import extract_metadata
from .norms_checker import NormsChecker
from .documentRepository.database_models import SessionLocal,RuleDB, DocumentDB, DocumentDependency # 导入 DocumentDB 和 DocumentDependency
from .documentRepository.document_storage import DocumentStorage
from .relationshipExtractor.dependency_builder_byMeta import DependencyBuilderByMeta
from .ai_retrieval.ingestor import DocumentIngestor # 导入 DocumentIngestor
from .ai_retrieval.vector_db_manager import VectorDBManager # 导入 VectorDBManager
from .ai_retrieval.retriever import Retriever # 导入 DocumentRetriever
from .ai_retrieval.embedder import EmbeddingComponent

from .api.models.rule_models import Rule, RuleCreate, RuleUpdate
import re

class FileAssiant:
    def __init__(self):
        self._Ingeser = IngestionCoordinator()
        self._checker = None
        self._db = SessionLocal()
        self._document_storage = DocumentStorage(self._db) # 实例化 DocumentStorage
        self._document_ingestor = DocumentIngestor() # 实例化 DocumentIngestor
        self._vector_db_manager = VectorDBManager() # 实例化 VectorDBManager
        # self._embedding_component = EmbeddingComponent() # 实例化 EmbeddingComponent
        # self._retriever = Retriever(embedding_component=self._embedding_component, vector_db_manager=self._vector_db_manager) # 实例化 Retriever
        self._embedding_component = None
        self._retriever = None
    # 激活合规检查
    def activate_norms_checker(self):
        self._checker = NormsChecker(self._db)

    # 1.检查文件格式
    def check_file_type(self, source_type: str, source_identifier: str) -> str:
        self.activate_norms_checker()
        if self._checker is None:
            return "错误：合规检查器未激活"
        else:
            document = self._Ingeser.ingest(source_type, source_identifier)
            if document is None:
                return "错误：文件读取失败"
            else:
                check_result = self._checker.check_text_norms(document.cleaned_text)
                if check_result.passed:
                    print("Document conforms to norms.")
                    # 成功 返回文档信息
                    return f"Document '{document.title}' ({document.id}) passed norm check."
                else:
                    print("Document does not conform to norms.")
                    # 失败 返回错误信息
                    return f"Document '{document.title}' ({document.id}) failed norm check. Summary: {check_result.summary}"
    
    # 1‘.是否符合规则
    def is_file_conform_rule(self, document: Document) -> bool:
        self.activate_norms_checker()
        if self._checker is None:
            print("错误：合规检查器未激活")
            return False
        else:
            check_result = self._checker.check_text_norms(document.cleaned_text)
            if check_result.passed:
                print("Document conforms to norms.")
                # 成功 返回文档信息
                print(f"Document '{document.title}' ({document.id}) passed norm check.")
                return True
            else:
                print("Document does not conform to norms.")
                # 失败 返回错误信息
                print(f"Document '{document.title}' ({document.id}) failed norm check. Summary: {check_result.summary}")
                return False


    # 2.读取并清洗数据 >> 检验rules >> 存入数据库 >> 生成向量 >> 返回成功信息            
    def upload_file(self, source_type: str, source_identifier: str):
        document = self._Ingeser.ingest(source_type, source_identifier)
        if document is None:
            return "错误：文件读取失败"
        else:
            if self.is_file_conform_rule(document):
                try:
                    document_storage = DocumentStorage(self._db)
                    # 3. 将文档存储到数据库 (upsert)
                    document_storage.upsert_document(document)
                    print(f"Document '{document.title}' ({document.id}) stored successfully after norm check.")
                    # 4. 触发依赖关系构建 (异步或同步)
                    # 注意：依赖关系构建通常需要文档已经在数据库中，以便进行反向查找
                    # 因此将其放在存储之后是合理的
                    dependency_builder = DependencyBuilderByMeta(self._db)
                    # 依赖构建器需要文档 ID
                    dependency_builder.build_dependencies_for_document_byId(document.id)
                    print(f"Dependency building triggered for {document.id}")
                    # 构建向量
                    try:
                        document_metadata = document.metadata if isinstance(document.metadata, dict) else {}
                        self._document_ingestor.ingest_document(
                            document_text=document.cleaned_text,
                            document_id=document.id,
                            document_metadata=document_metadata
                        )
                        # 向量化成功后，更新数据库中的 is_Vectorlized 字段
                        db_document = self._db.query(DocumentDB).filter(DocumentDB.id == document.id).first()
                        if db_document:
                            db_document.is_Vectorlized = True #type: ignore
                            self._db.commit()
                            print(f"Document '{document.id}' marked as vectorized in database.")
                        else:
                            print(f"Warning: Document '{document.id}' not found in database after vectorization.")

                        print(f"Success: Document ingested, stored, dependencies built,vectorlize successfully after passing norm check.")
                    except Exception as e:
                        print(f"Error vectorizing document {document.id}: {e}")
                        return "Success: Document ingested, stored, and dependencies built successfully after passing norm check.but vector build failed."
                except Exception as e:
                # 存储失败，回滚事务并抛出异常
                    self._db.rollback()
                    return f"Error: Failed to store document in database after norm check: {e}"
                return ""
            else:
                return "错误：文件不符合规范"

    # 2.1 上传文本
    def upload_text(self, text: str, title: str = "Untitled"):
        ref = extract_metadata(text)
        metaData = {
            'reference': ref
        }
        # 创建一个临时的 Document 对象
        document = Document(
            id = "",
            source_type = "text_str",
            source_identifier = f"text_str/{title}",
            raw_content = text,
            metadata = metaData,
            title = title, 
            cleaned_text = text
        )
        try:
            # 3. 将文档存储到数据库 (upsert)
            document_storage = DocumentStorage(self._db)
            document_storage.upsert_document(document)
            # 4. 触发依赖关系构建 (异步或同步)
            # 注意：依赖关系构建通常需要文档已经在数据库中，以便进行反向查找
            # 因此将其放在存储之后是合理的
            dependency_builder = DependencyBuilderByMeta(self._db)
            # 依赖构建器需要文档 ID
            dependency_builder.build_dependencies_for_document_byId(document.id)
            print(f"Dependency building triggered for {document.id}")
            return "Success: Document ingested, stored, and dependencies built successfully."
        except Exception as e:
            # 存储失败，回滚事务并抛出异常
            self._db.rollback()
            return f"Error: Failed to store document in database: {e}"


    # 3.批量上传
    def batch_upload_files(self, directory_path: str):
        results = {}
        if not os.path.isdir(directory_path):
            return f"错误：'{directory_path}' 不是一个有效的文件夹路径"

        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                print(f"Uploading file: {file_path}")
                result = self.upload_file(source_type='local_file', source_identifier=file_path)
                results[file_path] = result
                print(f"Result for {file_path}: {result}")
        return results
    
    #    4.增加检测规则
    #   {
    #     "name": "MyNewRule",
    #     "description": "This is a description for my new rule.",
    #     "type": "keyword_check",
    #     "pattern_config": {
    #                          "keywords": [
    #                            "背景",
    #                            "埋点"
    #                          ],
    #                          "match_type": "must_include"
    #                        }
    #     "severity": "ERROR",
    #     "is_active": true
    #   }
    # 4.增加检测规则
    def add_rule(self, rule: dict) -> str:
        rule_instance = RuleCreate(**rule)
        db_rule = RuleDB(
            name=rule_instance.name,
            description=rule_instance.description,
            type=rule_instance.type,
            pattern_config=rule_instance.pattern_config,
            severity=rule_instance.severity,
            is_active=rule_instance.is_active       
        )
        self._db.add(db_rule)
        self._db.commit()
        return f"Rule '{db_rule.name}' added successfully."

    # 4.1 设置规则的状态
    def set_rule_status(self, rule_name: str, is_active: bool) -> str:
        rule = self._db.query(RuleDB).filter(RuleDB.name == rule_name).first()
        if rule is None:
            return f"Rule with name: {rule_name} not found."
        setattr(rule, 'is_active', is_active) # 使用 setattr 函数进行赋值
        self._db.commit()
        return f"Rule {rule_name} status updated to {is_active}."

    # 5.构建所有依赖
    def build_all_dependency(self) -> str:
        dependency_builder = DependencyBuilderByMeta(self._db)
        dependency_builder.build_dependencies_for_all_documents()
        return "All dependencies built successfully."

    # 6.为数据库中的所有数据向量化
    # 根据ID判断，如果向量化数据库中记录了这个ID，则已经存在，否则进行向量话
    def vectorize_all_documents(self):
        """
        遍历关系型数据库中的所有文档，如果文档尚未向量化，则进行向量化。
        """
        print("\n--- Starting vectorization of all documents ---")
        # 从关系型数据库中获取所有文档的 ID 和内容
        # 注意：这里需要从 DocumentDB 中获取 cleaned_text 和 document_metadata
        # 假设 DocumentDB 包含这些字段
        self._embedding_component = EmbeddingComponent() # 实例化 EmbeddingComponent
        all_documents_in_db = self._db.query(DocumentDB).all()

        vectorized_count = 0
        skipped_count = 0

        for doc_db in all_documents_in_db:
            document_id = doc_db.id
            document_text = doc_db.cleaned_text
            # 确保 document_metadata 是一个字典类型
            document_metadata = doc_db.document_metadata if isinstance(doc_db.document_metadata, dict) else {}

            if self._vector_db_manager.document_exists_in_vector_db(str(document_id)):
                print(f"Document '{document_id}' already exists in vector DB. Skipping.")
                skipped_count += 1
            else:
                print(f"Vectorizing document: {document_id}")
                try:
                    # 使用 DocumentIngestor 进行向量化
                    self._document_ingestor.ingest_document(
                        document_text=str(document_text),
                        document_id=str(document_id),
                        document_metadata=document_metadata
                    )
                    vectorized_count += 1
                except Exception as e:
                    print(f"Error vectorizing document {document_id}: {e}")
        
        print(f"\n--- Vectorization complete. Total vectorized: {vectorized_count}, Skipped: {skipped_count} ---")
        return f"Vectorization complete. Total vectorized: {vectorized_count}, Skipped: {skipped_count}."

    # 6.1 更新向量化数据库
    def update_vec_database(self) -> str:
        """
        遍历关系型数据库中的所有文档，如果文档尚未向量化，则进行向量化。
        """
        
        print("\n--- Starting update vectorization of all documents ---")
        self._embedding_component = EmbeddingComponent() # 实例化 EmbeddingComponent

        # 查询所有 is_Vectorlized 为 False 的文档
        documents_to_vectorize = self._db.query(DocumentDB).filter(DocumentDB.is_Vectorlized == False).all() # type: ignore

        vectorized_count = 0
        skipped_count = 0
        failed_count = 0

        for doc_db in documents_to_vectorize:
            document_id = doc_db.id
            document_text = doc_db.cleaned_text
            document_metadata = doc_db.document_metadata if isinstance(doc_db.document_metadata, dict) else {}

            if self._vector_db_manager.document_exists_in_vector_db(str(document_id)):
                print(f"Document '{document_id}' already exists in vector DB. Skipping.")
                # 如果向量数据库中已存在，但关系型数据库中 is_Vectorlized 为 False，则更新关系型数据库
                if not doc_db.is_Vectorlized: # type: ignore
                    doc_db.is_Vectorlized = True # type: ignore
                    print(f"Updated is_Vectorlized for '{document_id}' to True.")
                skipped_count += 1
            else:
                print(f"Vectorizing document: {document_id}")
                try:
                    self._document_ingestor.ingest_document(
                        document_text=str(document_text),
                        document_id=str(document_id),
                        document_metadata=document_metadata
                    )
                    doc_db.is_Vectorlized = True # type: ignore
                    vectorized_count += 1
                except Exception as e:
                    print(f"Error vectorizing document {document_id}: {e}")
                    self._db.rollback()
                    failed_count += 1
        
        self._db.commit()
        return f"Update vectorization complete. Total vectorized: {vectorized_count}, Skipped: {skipped_count}, Failed: {failed_count}."
        return ""
    
    # 7.从向量数据库中检索
    def retrieve_from_vector_db(self, query_text: str, top_k: int = 5) -> list:
        """
        使用给定的查询文本从向量数据库中检索最相似的文本块。
        """
        if not query_text:
            return []
        self._embedding_component = EmbeddingComponent() # 实例化 EmbeddingComponent
        self._retriever = Retriever(embedding_component=self._embedding_component, vector_db_manager=self._vector_db_manager) # 实例化 Retriever
        results = self._retriever.retrieve_relevant_chunks(query_text, top_k)
        return results

    # 8. 结合依赖关系进行检索
    def retrieve_with_dependencies(self, query_text: str, top_k: int = 3) -> list:
        """
        首先从向量数据库中检索相关内容，然后根据这些内容的文档依赖关系，
        在依赖文档的向量中再次搜索原始查询，并将所有结果整合返回。
        """
        if not query_text:
            return []
        self._embedding_component = EmbeddingComponent() # 实例化 EmbeddingComponent
        self._retriever = Retriever(embedding_component=self._embedding_component, vector_db_manager=self._vector_db_manager) # 实例化 Retriever
        # 1. 初步检索
        initial_results = self._retriever.retrieve_relevant_chunks(query_text, top_k)
        all_results = list(initial_results) # 复制一份，避免修改原始迭代器

        # 提取初步检索结果中的文档ID
        initial_document_ids = {re.sub(r'^[^:]+:', '', result['metadata'].get('document_id')) 
                                for result in initial_results 
                                if result['metadata'].get('document_id')}

        # 2. 查询依赖关系并进行二次检索
        dependent_doc_ids = set()
        for doc_id in initial_document_ids:
            # 查询该文档的所有依赖文档
            dependencies = self._db.query(DocumentDependency).filter(
                (DocumentDependency.source_document_id == doc_id) | 
                (DocumentDependency.target_document_ids.contains(doc_id)) # 检查 doc_id 是否在 target_document_ids 列表中
            ).all()

            for dep in dependencies:
                if bool(dep.source_document_id == doc_id):
                    # dependent_doc_ids.update(dep.target_document_ids)
                    pass
                else:
                    # 如果 doc_id 是 target，那么 source 也是其依赖
                    dependent_doc_ids.add(dep.source_document_id)
        
        # 排除已经初步检索过的文档ID，避免重复检索
        dependent_doc_ids = dependent_doc_ids - initial_document_ids

        for dep_doc_id in dependent_doc_ids:
            # 对每个依赖文档进行二次检索
            # 这里可以考虑对二次检索的 top_k 进行调整，或者只检索与依赖文档ID相关的块
            # 为了简化，我们直接使用原始查询和 top_k 进行检索，并添加过滤条件
            secondary_results = self._retriever.retrieve_relevant_chunks(
                query_text=query_text,
                top_k=1,
                filter_metadata={'document_id': str(dep_doc_id)} # 过滤只检索特定文档的块
            )
            all_results.extend(secondary_results)
            
        # 对所有结果进行去重（如果需要）和排序（例如按距离）
        # 这里简单地将所有结果合并，实际应用中可能需要更复杂的去重和排序逻辑
        # 例如，可以根据 'id' 字段去重，并根据 'distance' 字段排序
        unique_results = {}
        for res in all_results:
            if res.get('id') not in unique_results or res.get('distance', float('inf')) < unique_results[res.get('id')].get('distance', float('inf')):
                unique_results[res.get('id')] = res
        
        sorted_results = sorted(unique_results.values(), key=lambda x: x.get('distance', float('inf')))

        return sorted_results