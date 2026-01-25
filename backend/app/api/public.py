from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.account import StatsResponse
from app.crud.account import get_stats

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/stats", response_model=StatsResponse)
async def get_public_stats(db: Session = Depends(get_db)):
    """
    Returns only aggregated statistics.
    No individual account data is exposed for security.
    """
    return get_stats(db)
