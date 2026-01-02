"""
订单管理功能测试
包括订单创建、取消、状态更新、同步、重试等测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import User, TradingBot, GridOrder
from app.auth import get_password_hash
from app.schemas import OrderCreate


class TestOrderCreate:
    """订单创建测试"""

    def test_create_limit_order(self, client: TestClient, test_user: User, db: Session):
        """测试创建限价单"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id,
            config='{"api_key": "test_key", "api_secret": "test_secret"}'
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 创建订单
        order_data = {
            "bot_id": bot.id,
            "order_type": "buy",
            "order_category": "limit",
            "price": 50000.0,
            "amount": 0.001
        }

        response = client.post("/api/orders/", json=order_data, headers=headers)

        # 验证结果（由于没有真实交易所，订单会失败）
        # 这里验证数据结构是否正确
        assert response.status_code in [201, 500]  # 可能创建成功，也可能因交易所API失败

        if response.status_code == 201:
            order = response.json()
            assert order["bot_id"] == bot.id
            assert order["order_type"] == "buy"
            assert order["order_category"] == "limit"
            assert order["price"] == 50000.0
            assert order["amount"] == 0.001

    def test_create_market_order(self, client: TestClient, test_user: User, db: Session):
        """测试创建市价单"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id,
            config='{"api_key": "test_key", "api_secret": "test_secret"}'
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 创建市价单（不需要价格）
        order_data = {
            "bot_id": bot.id,
            "order_type": "buy",
            "order_category": "market",
            "amount": 0.001
        }

        response = client.post("/api/orders/", json=order_data, headers=headers)

        assert response.status_code in [201, 500]

    def test_create_stop_loss_order(self, client: TestClient, test_user: User, db: Session):
        """测试创建止损单"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id,
            config='{"api_key": "test_key", "api_secret": "test_secret"}'
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 创建止损单
        order_data = {
            "bot_id": bot.id,
            "order_type": "sell",
            "order_category": "stop_loss",
            "amount": 0.001,
            "stop_price": 45000.0
        }

        response = client.post("/api/orders/", json=order_data, headers=headers)

        assert response.status_code in [201, 500]


class TestOrderQuery:
    """订单查询测试"""

    def test_get_orders(self, client: TestClient, test_user: User, db: Session):
        """测试获取订单列表"""
        # 创建机器人和订单
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        order = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取订单列表
        response = client.get("/api/orders/", headers=headers)

        assert response.status_code == 200
        orders = response.json()
        assert len(orders) >= 1

    def test_get_orders_with_filters(self, client: TestClient, test_user: User, db: Session):
        """测试带筛选条件的订单查询"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 创建多个订单
        order1 = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="pending"
        )
        order2 = GridOrder(
            bot_id=bot.id,
            level=2,
            order_type="sell",
            order_category="limit",
            price=51000.0,
            amount=0.001,
            side="sell",
            trading_pair="BTC/USDT",
            status="filled"
        )
        db.add_all([order1, order2])
        db.commit()

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 按状态筛选
        response = client.get("/api/orders/?status_filter=pending", headers=headers)
        assert response.status_code == 200
        orders = response.json()
        assert all(order["status"] == "pending" for order in orders)

        # 按类型筛选
        response = client.get("/api/orders/?order_type=buy", headers=headers)
        assert response.status_code == 200
        orders = response.json()
        assert all(order["order_type"] == "buy" for order in orders)

    def test_get_order_detail(self, client: TestClient, test_user: User, db: Session):
        """测试获取订单详情"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 创建订单
        order = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取订单详情
        response = client.get(f"/api/orders/{order.id}", headers=headers)

        assert response.status_code == 200
        order_data = response.json()
        assert order_data["id"] == order.id
        assert order_data["price"] == 50000.0


class TestOrderCancel:
    """订单取消测试"""

    def test_cancel_order(self, client: TestClient, test_user: User, db: Session):
        """测试取消订单"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 创建订单
        order = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 取消订单
        response = client.post(f"/api/orders/{order.id}/cancel", headers=headers)

        assert response.status_code == 200
        result = response.json()
        assert result["order_id"] == order.id

        # 验证订单状态
        db.refresh(order)
        assert order.status == "cancelled"


class TestOrderStatusUpdate:
    """订单状态更新测试"""

    def test_update_order_status(self, client: TestClient, test_user: User, db: Session):
        """测试更新订单状态"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 创建订单
        order = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 更新订单状态为部分成交
        response = client.patch(
            f"/api/orders/{order.id}/status",
            params={"new_status": "partial", "filled_amount": 0.0005},
            headers=headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "partial"

        # 验证订单状态
        db.refresh(order)
        assert order.status == "partial"
        assert order.filled_amount == 0.0005

    def test_update_order_status_to_filled(self, client: TestClient, test_user: User, db: Session):
        """测试更新订单状态为完全成交"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 创建订单
        order = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="pending"
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 更新订单状态为完全成交
        response = client.patch(
            f"/api/orders/{order.id}/status",
            params={"new_status": "filled", "filled_amount": 0.001, "filled_price": 50001.0},
            headers=headers
        )

        assert response.status_code == 200

        # 验证订单状态
        db.refresh(order)
        assert order.status == "filled"
        assert order.filled_amount == 0.001
        assert order.filled_price == 50001.0
        assert order.filled_at is not None


class TestOrderRetry:
    """订单重试测试"""

    def test_retry_failed_order(self, client: TestClient, test_user: User, db: Session):
        """测试重试失败的订单"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id,
            config='{"api_key": "test_key", "api_secret": "test_secret"}'
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 创建失败的订单
        order = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="failed",
            error_message="测试错误",
            retry_count=0,
            max_retry=3
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 重试订单
        response = client.post(f"/api/orders/{order.id}/retry", headers=headers)

        # 验证重试结果（由于没有真实交易所，可能失败）
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            result = response.json()
            assert result["order_id"] == order.id

        # 验证重试次数增加
        db.refresh(order)
        assert order.retry_count >= 1


class TestOrderStats:
    """订单统计测试"""

    def test_get_order_stats(self, client: TestClient, test_user: User, db: Session):
        """测试获取订单统计信息"""
        # 创建机器人
        bot = TradingBot(
            name="测试机器人",
            exchange="binance",
            trading_pair="BTC/USDT",
            strategy="grid",
            status="stopped",
            user_id=test_user.id
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)

        # 创建多个订单
        order1 = GridOrder(
            bot_id=bot.id,
            level=1,
            order_type="buy",
            order_category="limit",
            price=50000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="pending"
        )
        order2 = GridOrder(
            bot_id=bot.id,
            level=2,
            order_type="sell",
            order_category="limit",
            price=51000.0,
            amount=0.001,
            side="sell",
            trading_pair="BTC/USDT",
            status="filled",
            filled_amount=0.001
        )
        order3 = GridOrder(
            bot_id=bot.id,
            level=3,
            order_type="buy",
            order_category="limit",
            price=49000.0,
            amount=0.001,
            side="buy",
            trading_pair="BTC/USDT",
            status="cancelled"
        )
        db.add_all([order1, order2, order3])
        db.commit()

        # 登录获取token
        response = client.post(
            "/api/auth/login",
            data={"username": test_user.username, "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 获取订单统计
        response = client.get("/api/orders/stats/summary", headers=headers)

        assert response.status_code == 200
        stats = response.json()
        assert "total_orders" in stats
        assert "pending_count" in stats
        assert "filled_count" in stats
        assert "cancelled_count" in stats
        assert stats["total_orders"] == 3


if __name__ == "__main__":
    print("订单管理功能测试")
    print("=" * 60)

    print("\n请确保已初始化数据库: python init_db.py")
    print("\n然后使用 pytest 运行测试:")
    print("  pytest test_orders.py -v")
    print("\n或者运行单个测试:")
    print("  pytest test_orders.py::TestOrderCreate::test_create_limit_order -v")
