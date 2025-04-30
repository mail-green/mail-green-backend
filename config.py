import os

class Config:
    # Gmail API
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'your-client-id')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'your-client-secret')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')
    
    # # Redis/Celery
    # REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # # 기타 설정
    # DEBUG = os.getenv('DEBUG', 'true').lower() == 'true' 