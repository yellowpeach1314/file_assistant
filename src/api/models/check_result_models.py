from pydantic import BaseModel
from typing import List, Optional, Any
from .rule_models import RuleSeverity # 导入规则严重程度

class NormViolation(BaseModel):
    """
    表示一个规范违规项
    """
    rule_id: int # 违规的规则 ID
    rule_name: str # 违规的规则名称
    severity: RuleSeverity # 违规的严重程度
    description: str # 违规描述
    location: Optional[str] = None # 违规在文档中的位置描述 (e.g., "Line 10", "Section 'Background'")
    suggested_fix: Optional[str] = None # 建议的修复方法
    details: Optional[Any] = None # 其他详细信息 (e.g., 匹配到的关键词)

class NormCheckResult(BaseModel):
    """
    文档规范检查的整体结果报告
    """
    document_id: str # 被检查文档的 ID
    violations: List[NormViolation] # 所有违规项的列表
    passed: bool # 是否通过所有 ERROR 级别的检查
    summary: str # 检查总结 (e.g., "检查完成，发现 3 个 WARNING 和 1 个 ERROR")