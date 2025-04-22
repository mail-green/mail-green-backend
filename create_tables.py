# create_tables.py
from database import Base, engine
from models import User  # 필요한 모델들을 import

Base.metadata.create_all(bind=engine)
