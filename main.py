from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

app = FastAPI()

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()
