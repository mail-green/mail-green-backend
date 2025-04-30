from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from logger import get_logger

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger("user_controller")

@router.get("/")
def read_users(db: Session = Depends(get_db)):
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        logger.error(f"사용자 목록 조회 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 