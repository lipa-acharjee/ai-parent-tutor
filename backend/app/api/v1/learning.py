from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Question, Attempt, Child, Family
from app.core.security import get_current_user
from app.schemas.learning import AnswerRequest
from app.ai.service import evaluate_answer

router=APIRouter()
@router.post("/answer")
async def answer(body:AnswerRequest,db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    fam=(await db.execute(select(Family).where(Family.owner_id==user.id))).scalar_one()
    child=(await db.execute(select(Child).where(Child.id==body.child_id,Child.family_id==fam.id))).scalar_one_or_none()
    q=(await db.execute(select(Question).where(Question.id==body.question_id))).scalar_one_or_none()
    if not child or not q: raise HTTPException(404,"Question or child not found")
    result=evaluate_answer(q.question,q.expected_answer,body.answer)
    db.add(Attempt(question_id=q.id,child_id=child.id,answer=body.answer,score=result["score"],feedback=result)); await db.commit()
    return result

