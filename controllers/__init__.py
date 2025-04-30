from fastapi import APIRouter
from .auth_controller import router as auth_router
from .gmail_controller import router as gmail_router
from .user_controller import router as user_router

# 모든 라우터를 하나의 리스트로 관리
routers = [
    auth_router,
    user_router,
    gmail_router,
] 