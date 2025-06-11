import re
# 导入 Callable 和 cast
from typing import List, Dict, Any, Callable, cast, Optional
# 移除 Integer 导入，因为它没有被直接使用
# from sqlalchemy import Integer
from sqlalchemy.orm import Session

# 导入数据库模型和 Pydantic 模型
from .documentRepository.database_models import DocumentDB, RuleDB
from .api.models.check_result_models import NormCheckResult, NormViolation
# 直接导入 RuleSeverity 类型，而不是 RuleSeverity 类
from .api.models.rule_models import RuleSeverity

class NormsChecker:
    """
    文档规范检查器
    """
    def __init__(self, db: Session):
        self.db = db
        # 注册不同规则类型的处理函数
        # 修改类型提示为 Callable 并指定参数和返回值类型
        self._rule_handlers: Dict[str, Callable[[str, RuleDB], List[NormViolation]]] = {
            'keyword_check': self._check_keyword,
            'llm_check': self._check_llm,
            # TODO: 添加其他规则类型的处理函数
            # 'structure_check': self._check_structure,
            # 'length_check': self._check_length,
            # ...
        }

    def check_document_norms(self, document_id: str) -> NormCheckResult:
        """
        对指定文档执行规范检查

        Args:
            document_id: 要检查的文档 ID

        Returns:
            NormCheckResult: 规范检查报告
        """
        # 1. 从数据库加载文档的 cleaned_text
        document = self.db.query(DocumentDB).filter(DocumentDB.id == document_id).first()
        if not document:
            # 如果文档不存在，返回一个空的或错误报告
            return NormCheckResult(
                document_id=document_id,
                violations=[],
                passed=False,
                summary=f"Error: Document with ID {document_id} not found."
            )

        cleaned_text = document.cleaned_text or ""

        # 2. 从数据库加载所有激活的规则
        active_rules: List[RuleDB] = self.db.query(RuleDB).filter(RuleDB.is_active == True).all()

        violations: List[NormViolation] = []

        # 3. 遍历规则并执行检查
        for rule in active_rules:
            # 确保 rule.type 是字符串用于字典查找
            handler = self._rule_handlers.get(str(rule.type))
            if handler:
                # 调用对应的规则处理函数
                # 确保 cleaned_text 是字符串
                rule_violations = handler(str(cleaned_text), rule)
                violations.extend(rule_violations)
            else:
                # 如果规则类型没有对应的处理函数，记录一个警告
                violations.append(NormViolation(
                    # 使用 cast 明确类型
                    rule_id=cast(int, rule.id),
                    rule_name=cast(str, rule.name),
                    # 直接使用字符串字面量
                    severity="WARNING",
                    description=f"Unsupported rule type: {rule.type}",
                    location=None,
                    suggested_fix="Implement a handler for this rule type.",
                    details={"rule_config": rule.pattern_config}
                ))

        # 4. 生成检查报告总结
        # 直接使用字符串字面量进行比较
        error_count = sum(1 for v in violations if v.severity == "ERROR")
        warning_count = sum(1 for v in violations if v.severity == "WARNING")
        info_count = sum(1 for v in violations if v.severity == "INFO")

        summary = f"Norm check completed for document {document_id}. Found {error_count} ERRORs, {warning_count} WARNINGs, and {info_count} INFOs."
        passed = error_count == 0 # 如果没有 ERROR 级别的违规，则认为通过检查

        return NormCheckResult(
            document_id=document_id,
            violations=violations,
            passed=passed,
            summary=summary
        )

    def check_text_norms(self, text: str) -> NormCheckResult:
        """
        对输入的文本执行规范检查
        Args:
            text: 要检查的文本内容
        Returns:
            NormCheckResult: 规范检查报告
        """
        # 1. 从数据库加载所有激活的规则
        active_rules: List[RuleDB] = self.db.query(RuleDB).filter(RuleDB.is_active == True).all()
        violations: List[NormViolation] = []

        # 2. 遍历规则并执行检查
        for rule in active_rules:
            handler = self._rule_handlers.get(str(rule.type))
            if handler:
                # 调用对应的规则处理函数
                rule_violations = handler(text, rule)
                violations.extend(rule_violations)
            else:
                # 如果规则类型没有对应的处理函数，记录一个警告
                violations.append(NormViolation(
                    rule_id=cast(int, rule.id),
                    rule_name=cast(str, rule.name),
                    severity="WARNING",
                    description=f"Unsupported rule type: {rule.type}",
                    location=None,
                    suggested_fix="Implement a handler for this rule type.",
                    details={"rule_config": rule.pattern_config}
                ))

        # 3. 生成检查报告总结
        error_count = sum(1 for v in violations if v.severity == "ERROR")
        warning_count = sum(1 for v in violations if v.severity == "WARNING")
        info_count = sum(1 for v in violations if v.severity == "INFO")

        # 对于直接文本检查，document_id 可以设置为 None 或一个特殊值
        summary = f"Norm check completed for input text. Found {error_count} ERRORs, {warning_count} WARNINGs, and {info_count} INFOs."
        passed = error_count == 0
        print(summary)
        # 打印每一个NormViolation的severity和description
        for violation in violations:
            print(f"Severity: {violation.severity}, Description: {violation.description}")
        return NormCheckResult(
            # document_id 可以设置为 None 或一个表示非数据库文档的标识符
            document_id="",
            violations=violations,
            passed=passed,
            summary=summary
        )


    # --- 规则处理函数的示例 ---

    def _check_keyword(self, text: str, rule: RuleDB) -> List[NormViolation]:
        """
        处理 'keyword_check' 类型的规则
        rule.pattern_config 应该包含一个 'keywords' 列表和一个 'match_type' (e.g., 'must_include', 'must_not_include')
        """
        violations: List[NormViolation] = []
        config = rule.pattern_config
        # if not config or 'keywords' not in config or 'match_type' not in config: # 原代码
        # 检查 config 是否为 None 或不是字典，以及是否缺少必要的键
        # 对于类型检查器，可能需要对 config 进行 cast
        if not isinstance(cast(dict, config), dict) or 'keywords' not in cast(dict, config) or 'match_type' not in cast(dict, config):
             violations.append(NormViolation(
                # 使用 cast 明确类型
                rule_id=cast(int, rule.id),
                rule_name=cast(str, rule.name),
                # 直接使用字符串字面量
                severity="ERROR",
                description="Invalid configuration for keyword_check rule.",
                location=None,
                suggested_fix="Update the rule's pattern_config to include 'keywords' (list) and 'match_type' (string).",
                details={"config": config}
            ))
             return violations


        keywords = cast(dict, config).get('keywords', []) # 使用 .get() 提供默认值，避免 KeyError
        match_type = cast(dict, config).get('match_type')

        # 检查 keywords 是否是列表
        if not isinstance(keywords, list):
             violations.append(NormViolation(
                rule_id=cast(int, rule.id), # 使用 cast 明确类型
                rule_name=cast(str, rule.name), # 使用 cast 明确类型
                severity="ERROR",
                description="Invalid configuration for keyword_check rule: 'keywords' must be a list.",
                location=None,
                suggested_fix="Update the rule's pattern_config: 'keywords' should be a list of strings.",
                details={"config": config}
            ))
             return violations


        if match_type == 'must_include':
            missing_keywords = [kw for kw in keywords if kw not in text]
            if missing_keywords:
                violations.append(NormViolation(
                    rule_id=cast(int, rule.id), # 使用 cast 明确类型
                    rule_name=cast(str, rule.name), # 使用 cast 明确类型
                    severity=cast(RuleSeverity,rule.severity), # 使用规则定义的严重程度
                    description=cast(Optional[str], rule.description) or f"Document must include keywords: {', '.join(keywords)}",
                    location="Document body",
                    suggested_fix=f"Add the following keywords to the document: {', '.join(missing_keywords)}",
                    details={"missing_keywords": missing_keywords}
                ))
        elif match_type == 'must_not_include':
            found_keywords = [kw for kw in keywords if kw in text]
            if found_keywords:
                violations.append(NormViolation(
                    rule_id=cast(int, rule.id), # 使用 cast 明确类型
                    rule_name=cast(str, rule.name), # 使用 cast 明确类型
                    severity=cast(RuleSeverity,rule.severity), # 使用规则定义的严重程度
                    description=cast(Optional[str], rule.description) or f"Document must include keywords: {', '.join(keywords)}",
                    location="Document body", # TODO: 可以尝试找到关键词的具体位置
                    suggested_fix=f"Remove the following keywords from the document: {', '.join(found_keywords)}",
                    details={"found_keywords": found_keywords}
                ))
        # TODO: 添加其他 match_type，例如 'regex_match', 'regex_not_match' 等
        else:
             violations.append(NormViolation(
                rule_id=cast(int, rule.id), # 使用 cast 明确类型
                rule_name=cast(str, rule.name), # 使用 cast 明确类型
                # 直接使用字符串字面量
                severity="ERROR",
                description=f"Unsupported match_type for keyword_check rule: {match_type}.",
                location=None,
                suggested_fix="Update the rule's pattern_config match_type to 'must_include' or 'must_not_include'.",
                details={"config": config}
            ))
            
        return violations

    def _check_llm(self, text: str, rule: RuleDB) -> List[NormViolation]:
        violations: List[NormViolation] = []
        return violations

    # TODO: 实现其他规则类型的处理函数
    # def _check_structure(self, text: str, rule: RuleDB) -> List[NormViolation]:
    #     """处理 'structure_check' 类型的规则"""
    #     pass

    # def _check_length(self, text: str, rule: RuleDB) -> List[NormViolation]:
    #     """处理 'length_check' 类型的规则"""
    #     pass