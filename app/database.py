from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 根据数据库 URL 选择合适的驱动
database_url = settings.DATABASE_URL
if database_url.startswith('sqlite'):
    # SQLite 连接，显式使用 sqlite:// 驱动
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
elif database_url.startswith('postgresql'):
    # PostgreSQL 连接，确保使用 psycopg3
    if '+psycopg' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://')
    engine = create_engine(database_url)
else:
    # 其他数据库
    engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
