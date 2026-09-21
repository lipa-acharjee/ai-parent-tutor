from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Child, Family
from app.schemas.child import ChildCreate, ChildResponse
from app.core.security import get_current_user
router=APIRouter()
async def family_for(user,db): return (await db.execute(select(Family).where(Family.owner_id==user.id))).scalar_one()
@router.post("",response_model=ChildResponse)
async def create_child(body:ChildCreate,db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    fam=await family_for(user,db); c=Child(family_id=fam.id,**body.model_dump()); db.add(c); await db.commit(); await db.refresh(c); return c
@router.get("",response_model=list[ChildResponse])
async def list_children(db:AsyncSession=Depends(get_db),user=Depends(get_current_user)):
    fam=await family_for(user,db); return list((await db.execute(select(Child).where(Child.family_id==fam.id))).scalars().all())
