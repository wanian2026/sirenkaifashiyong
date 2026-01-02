"""
P2功能测试用例
测试系统管理、机器人管理增强等功能
"""

import pytest
import os
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 导入应用和依赖
from app.main import app
from app.database import get_db, Base
from app.models import User, TradingBot, Trade
from app.audit_log import AuditLog
from app.auth import get_password_hash
from app.log_manager import LogManager
from app.database_manager import DatabaseManager
from app.performance_monitor import PerformanceMonitor
from app.bot_performance import BotPerformanceTracker, BotConfigTemplate

# 测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_p2.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建测试客户端
client = TestClient(app)


# 数据库依赖覆盖
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# 测试夹具
@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_user(db):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="module")
def auth_headers(test_user):
    """获取认证头"""
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def test_bot(db, test_user):
    """创建测试机器人"""
    bot = TradingBot(
        name="Test Bot",
        exchange="binance",
        trading_pair="BTC/USDT",
        strategy="hedge_grid",
        config=json.dumps({
            "grid_levels": 10,
            "grid_spacing": 0.02,
            "investment_amount": 1000
        }),
        user_id=test_user.id,
        status="stopped"
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


# ========== 日志管理测试 ==========

def test_export_logs_to_csv(db, test_user, auth_headers):
    """测试导出日志到CSV"""
    # 创建一些审计日志
    for i in range(5):
        log = AuditLog(
            user_id=test_user.id,
            username=test_user.username,
            action="create",
            resource="bot",
            level="info",
            success=True,
            details=f"Test log {i}"
        )
        db.add(log)
    db.commit()

    # 导出日志
    response = client.get(
        "/api/logs/export/csv",
        headers=auth_headers
    )

    # 检查响应
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


def test_get_log_analysis_summary(db, auth_headers):
    """测试获取日志分析摘要"""
    response = client.get(
        "/api/logs/analysis/summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


def test_detect_log_anomalies(db, auth_headers):
    """测试检测日志异常"""
    response = client.get(
        "/api/logs/detection/anomalies",
        headers=auth_headers,
        params={"threshold": 10}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "total_anomalies" in data["data"]


# ========== 数据库管理测试 ==========

def test_create_database_backup(auth_headers):
    """测试创建数据库备份"""
    response = client.post(
        "/api/database/backup",
        headers=auth_headers,
        params={"description": "Test backup"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "backup_file" in data


def test_list_database_backups(auth_headers):
    """测试列出数据库备份"""
    response = client.get(
        "/api/database/backups",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


def test_get_database_stats(auth_headers):
    """测试获取数据库统计信息"""
    response = client.get(
        "/api/database/stats",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


# ========== 性能监控测试 ==========

def test_get_system_status(auth_headers):
    """测试获取系统状态"""
    response = client.get(
        "/api/performance/system-status",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "cpu" in data["data"]
    assert "memory" in data["data"]


def test_get_performance_summary(auth_headers):
    """测试获取性能摘要"""
    response = client.get(
        "/api/performance/summary",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


def test_check_system_health(auth_headers):
    """测试检查系统健康状态"""
    response = client.get(
        "/api/performance/health",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "status" in data["data"]
    assert "checks" in data["data"]


def test_start_stop_monitoring(auth_headers):
    """测试启动和停止监控"""
    # 启动监控
    start_response = client.post(
        "/api/performance/monitoring/start",
        headers=auth_headers,
        params={"interval": 5}
    )
    assert start_response.status_code == 200

    # 停止监控
    stop_response = client.post(
        "/api/performance/monitoring/stop",
        headers=auth_headers
    )
    assert stop_response.status_code == 200


# ========== 机器人管理增强测试 ==========

def test_batch_start_stop_bots(db, test_bot, auth_headers):
    """测试批量启停机器人"""
    # 创建第二个机器人
    bot2 = TradingBot(
        name="Test Bot 2",
        exchange="binance",
        trading_pair="ETH/USDT",
        strategy="hedge_grid",
        config=json.dumps({"grid_levels": 5}),
        user_id=test_bot.user_id,
        status="stopped"
    )
    db.add(bot2)
    db.commit()

    # 批量启动（预期会失败，因为没有实际的交易所连接）
    response = client.post(
        "/api/bots/batch/start",
        headers=auth_headers,
        json={"bot_ids": [test_bot.id, bot2.id]}
    )

    # 由于没有实际的交易所连接，启动会失败
    # 但API应该返回结果
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


def test_clone_bot(db, test_bot, auth_headers):
    """测试克隆机器人"""
    response = client.post(
        f"/api/bots/{test_bot.id}/clone",
        headers=auth_headers,
        params={"new_name": "Cloned Bot"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "Cloned Bot"
    assert data["exchange"] == test_bot.exchange
    assert data["trading_pair"] == test_bot.trading_pair


def test_batch_update_config(db, test_bot, auth_headers):
    """测试批量更新配置"""
    response = client.put(
        "/api/bots/batch/config",
        headers=auth_headers,
        json={"bot_ids": [test_bot.id], "config_update": {"grid_levels": 15}}
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data


# ========== 机器人性能管理测试 ==========

def test_get_bot_performance_stats(db, test_bot, auth_headers):
    """测试获取机器人性能统计"""
    # 创建一些交易记录
    for i in range(10):
        trade = Trade(
            bot_id=test_bot.id,
            order_id=f"order_{i}",
            trading_pair="BTC/USDT",
            side="buy",
            price=50000.0 + i * 100,
            amount=0.01,
            fee=5.0,
            profit=10.0 if i % 2 == 0 else -5.0
        )
        db.add(trade)
    db.commit()

    # 获取性能统计
    response = client.get(
        f"/api/bot-performance/{test_bot.id}/stats",
        headers=auth_headers,
        params={"days": 30}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "summary" in data["data"]
    assert "performance" in data["data"]


def test_get_bot_resource_usage(db, test_bot, auth_headers):
    """测试获取机器人资源使用情况"""
    response = client.get(
        f"/api/bot-performance/{test_bot.id}/resource-usage",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "orders" in data["data"]
    assert "trades" in data["data"]
    assert "system" in data["data"]


def test_compare_bots_performance(db, test_bot, auth_headers):
    """测试比较机器人性能"""
    # 克隆一个机器人用于比较
    bot2 = TradingBot(
        name="Test Bot 2",
        exchange="binance",
        trading_pair="BTC/USDT",
        strategy="hedge_grid",
        config=json.dumps({"grid_levels": 5}),
        user_id=test_bot.user_id,
        status="stopped"
    )
    db.add(bot2)
    db.commit()

    # 比较性能
    response = client.post(
        "/api/bot-performance/compare",
        headers=auth_headers,
        params={"bot_ids": [test_bot.id, bot2.id], "days": 30}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "comparisons" in data["data"]


# ========== 配置模板测试 ==========

def test_save_config_template(db, test_bot, auth_headers):
    """测试保存配置模板"""
    response = client.post(
        "/api/bot-templates",
        headers=auth_headers,
        params={
            "template_name": "Test Template",
            "bot_id": test_bot.id,
            "description": "Test template description"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "template_id" in data

    return data["template_id"]


def test_list_config_templates(auth_headers):
    """测试列出配置模板"""
    response = client.get(
        "/api/bot-templates",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_delete_config_template(auth_headers):
    """测试删除配置模板"""
    # 先保存一个模板
    save_response = client.post(
        "/api/bot-templates",
        headers=auth_headers,
        params={
            "template_name": "Template to Delete",
            "bot_id": 1,
            "description": "This will be deleted"
        }
    )
    template_id = save_response.json()["template_id"]

    # 删除模板
    response = client.delete(
        f"/api/bot-templates/{template_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# ========== 运行所有测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
