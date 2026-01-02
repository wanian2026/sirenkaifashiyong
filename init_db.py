from app.database import engine, Base
from app.models import User, TradingBot, GridOrder, Trade
from app.auth import get_password_hash


def init_database():
    """初始化数据库"""
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成!")

    # 创建默认管理员用户
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == "admin").first()
        if not existing_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123")
            )
            db.add(admin_user)
            db.commit()
            print("默认管理员用户已创建:")
            print("用户名: admin")
            print("密码: admin123")
            print("请登录后立即修改密码!")
        else:
            print("管理员用户已存在，跳过创建")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
