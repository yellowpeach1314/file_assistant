from typing import Optional, Any, Literal # 导入 Literal
from pydantic import BaseModel
from datetime import datetime

# 定义规则的严重程度，使用 Literal 指定允许的字符串值
RuleSeverity = Literal["INFO", "WARNING", "ERROR"]

# 用于创建规则的 Pydantic 模型
class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str # 规则类型 (e.g., 'keyword_check', 'structure_check')
    pattern_config: Any # 规则的具体配置/模式，可以是任意类型，后续可以定义更具体的模型
    severity: RuleSeverity = "INFO" # 严重程度，默认值直接使用字符串字面量
    is_active: bool = True # 是否激活

    class Config:
        # 允许使用 ORM 模型（如 SQLAlchemy 模型）的属性访问方式
        from_attributes = True

# 用于更新规则的 Pydantic 模型
class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    pattern_config: Optional[Any] = None
    severity: Optional[RuleSeverity] = None # 使用 RuleSeverity 类型
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True

# 用于读取规则的 Pydantic 模型（包含数据库生成的字段）
class Rule(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    type: str
    pattern_config: Any
    severity: RuleSeverity # 使用 RuleSeverity 类型
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True