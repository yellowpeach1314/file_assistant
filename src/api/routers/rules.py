from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

# 导入数据库模型和 Pydantic 模型
from ...documentRepository.database_models import RuleDB, SessionLocal
from ..models.rule_models import Rule, RuleCreate, RuleUpdate

# 创建 FastAPI 路由器
router = APIRouter(
    prefix="/rules",
    tags=["rules"],
    responses={404: {"description": "Not found"}},
)

# 依赖项：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 创建规则
@router.post("/", response_model=Rule, status_code=status.HTTP_201_CREATED)
def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
    db_rule = RuleDB(
        name=rule.name,
        description=rule.description,
        type=rule.type,
        pattern_config=rule.pattern_config,
        severity=rule.severity,
        is_active=rule.is_active
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

# 读取所有规则
@router.get("/", response_model=List[Rule])
def read_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rules = db.query(RuleDB).offset(skip).limit(limit).all()
    return rules

# 读取单个规则
@router.get("/{rule_id}", response_model=Rule)
def read_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return db_rule

# 更新规则
@router.put("/{rule_id}", response_model=Rule)
def update_rule(rule_id: int, rule: RuleUpdate, db: Session = Depends(get_db)):
    db_rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    # 更新字段，只更新 Pydantic 模型中非 None 的字段
    update_data = rule.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rule, key, value)

    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

# 删除规则
@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(RuleDB).filter(RuleDB.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    db.delete(db_rule)
    db.commit()
    return {"ok": True} # 返回一个简单的成功响应

# 使用说明
# curl -X DELETE http://localhost:8000/rules/2 删除 ID 为 2 的规则