from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from controllers import routers
from logger import get_logger
import os

# 환경변수 로드
load_dotenv()

# FastAPI 앱 초기화
app = FastAPI()
logger = get_logger("main")

# 세션 미들웨어 추가
app.add_middleware(SessionMiddleware, secret_key=os.getenv('JWT_SECRET_KEY'))

# 라우터 등록
for router in routers:
    app.include_router(router)