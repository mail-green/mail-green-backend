from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth_service import get_google_auth_flow, refresh_token
from logger import get_logger
from authlib.integrations.starlette_client import OAuth
import os

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("auth_controller")

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/gmail.readonly'
    }
)

@router.get('/google')
async def login_via_google(request: Request):
    redirect_uri = request.url_for('auth_google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/google/callback')
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        request.session['token'] = token  # 토큰을 세션에 저장
        resp = await oauth.google.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            token=token
        )
        user_info = resp.json()
        
        email = user_info.get("email")
        name = user_info.get("name")

        # DB에 사용자 정보가 없으면 새로 생성
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
        return {"id": user.id, "name": user.name, "email": user.email}
    except Exception as e:
        logger.error(f"Google 인증 콜백 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 