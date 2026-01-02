"""
Pytest 配置文件
提供数据库 fixture 和其他测试工具
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app.models import User
from app.auth import get_password_hash


# 测试数据库（内存数据库）
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    创建测试数据库会话

    每个测试函数都会获得一个独立的数据库会话
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # 清理：删除所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """
    创建测试客户端

    覆盖 get_db 依赖项以使用测试数据库
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db: Session):
    """
    创建测试用户

    Returns:
        User: 测试用户对象
    """
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        role="trader",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db: Session):
    """
    创建管理员用户

    Returns:
        User: 管理员用户对象
    """
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_user: User):
    """
    获取认证头

    Args:
        client: 测试客户端
        test_user: 测试用户

    Returns:
        dict: 包含 Authorization 头的字典
    """
    # 登录获取 token
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(client: TestClient, admin_user: User):
    """
    获取管理员认证头

    Args:
        client: 测试客户端
        admin_user: 管理员用户

    Returns:
        dict: 包含管理员 Authorization 头的字典
    """
    # 登录获取 token
    response = client.post(
        "/api/auth/login",
        data={
            "username": admin_user.username,
            "password": "admin123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
