import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import TranslationRule
from app.schemas import RuleCreate, RuleResponse, RuleUpdate
from app.services.rule_engine import reload as reload_rules

router = APIRouter(prefix="/admin/rules", tags=["admin"])


@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(rule: RuleCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(TranslationRule).where(TranslationRule.keyword == rule.keyword)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Keyword '{rule.keyword}' already exists",
        )
    db_rule = TranslationRule(keyword=rule.keyword, rule_text=rule.rule_text)
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    await reload_rules()
    return db_rule


@router.get("/", response_model=list[RuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TranslationRule).order_by(TranslationRule.updated_at.desc())
    )
    return result.scalars().all()


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str, rule: RuleUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        rule_uuid = uuid.UUID(rule_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rule_id format"
        )
    db_rule = await db.get(TranslationRule, rule_uuid)
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found"
        )
    if rule.keyword is not None:
        db_rule.keyword = rule.keyword
    if rule.rule_text is not None:
        db_rule.rule_text = rule.rule_text
    await db.commit()
    await db.refresh(db_rule)
    await reload_rules()
    return db_rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    try:
        rule_uuid = uuid.UUID(rule_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rule_id format"
        )
    db_rule = await db.get(TranslationRule, rule_uuid)
    if not db_rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found"
        )
    await db.delete(db_rule)
    await db.commit()
    await reload_rules()
