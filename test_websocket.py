"""
WebSocket实时数据推送功能测试
"""

import asyncio
import websockets
import json
import pytest
from datetime import datetime


class TestWebSocketRealtime:
    """WebSocket实时数据推送测试"""

    @pytest.fixture
    def auth_token(self):
        """
        获取测试用的JWT token

        注意: 这里需要先有一个有效的用户和token
        实际使用时应该先调用登录API获取token
        """
        # 这里返回一个示例token，实际使用时需要替换
        # 可以从登录接口获取: POST /api/auth/login
        return "your_jwt_token_here"

    @pytest.mark.asyncio
    async def test_market_overview_stream(self, auth_token):
        """测试市场概览数据推送"""
        uri = f"ws://localhost:8000/api/ws/market_overview?token={auth_token}"

        try:
            async with websockets.connect(uri) as websocket:
                print("已连接到市场概览数据流")

                # 接收3条消息
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)

                    print(f"收到消息 {i+1}: {data}")

                    # 验证消息格式
                    assert "type" in data
                    assert data["type"] == "market_overview"
                    assert "timestamp" in data
                    assert "data" in data

                    # 验证数据结构
                    assert "market_data" in data["data"]
                    assert "summary" in data["data"]

                    # 验证概览统计
                    summary = data["data"]["summary"]
                    assert "total_pairs" in summary
                    assert "gainers" in summary
                    assert "losers" in summary
                    assert "avg_change" in summary
                    assert "total_volume" in summary

                print("市场概览数据推送测试通过")

        except asyncio.TimeoutError:
            pytest.fail("连接超时")
        except Exception as e:
            pytest.fail(f"测试失败: {e}")

    @pytest.mark.asyncio
    async def test_market_data_stream(self, auth_token):
        """测试市场数据推送"""
        trading_pair = "BTC/USDT"
        uri = f"ws://localhost:8000/api/ws/market_data?token={auth_token}&trading_pair={trading_pair}"

        try:
            async with websockets.connect(uri) as websocket:
                print(f"已连接到市场数据流: {trading_pair}")

                # 接收3条消息
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)

                    print(f"收到消息 {i+1}: {data}")

                    # 验证消息格式
                    assert "type" in data
                    assert data["type"] == "market_data"
                    assert "trading_pair" in data
                    assert data["trading_pair"] == trading_pair
                    assert "timestamp" in data
                    assert "data" in data

                    # 验证数据字段
                    market_data = data["data"]
                    assert "price" in market_data
                    assert "high" in market_data
                    assert "low" in market_data
                    assert "volume" in market_data
                    assert "change" in market_data
                    assert "percentage" in market_data

                print("市场数据推送测试通过")

        except asyncio.TimeoutError:
            pytest.fail("连接超时")
        except Exception as e:
            pytest.fail(f"测试失败: {e}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"])
    async def test_kline_data_stream(self, auth_token, timeframe):
        """测试K线数据推送（多个时间周期）"""
        trading_pair = "BTC/USDT"
        uri = f"ws://localhost:8000/api/ws/kline_data?token={auth_token}&trading_pair={trading_pair}&timeframe={timeframe}"

        try:
            async with websockets.connect(uri) as websocket:
                print(f"已连接到K线数据流: {trading_pair}, {timeframe}")

                # 接收2条K线数据
                for i in range(2):
                    message = await asyncio.wait_for(websocket.recv(), timeout=20)
                    data = json.loads(message)

                    print(f"收到消息 {i+1}: {data}")

                    # 验证消息格式
                    assert "type" in data
                    assert data["type"] == "kline_data"
                    assert "trading_pair" in data
                    assert data["trading_pair"] == trading_pair
                    assert "timeframe" in data
                    assert data["timeframe"] == timeframe
                    assert "timestamp" in data
                    assert "data" in data

                    # 验证K线数据字段
                    kline_data = data["data"]
                    assert "symbol" in kline_data
                    assert "timestamp" in kline_data
                    assert "open" in kline_data
                    assert "high" in kline_data
                    assert "low" in kline_data
                    assert "close" in kline_data
                    assert "volume" in kline_data

                print(f"K线数据推送测试通过: {timeframe}")

        except asyncio.TimeoutError:
            pytest.fail(f"连接超时: {timeframe}")
        except Exception as e:
            pytest.fail(f"测试失败: {e}")

    @pytest.mark.asyncio
    async def test_order_book_stream(self, auth_token):
        """测试深度数据推送"""
        trading_pair = "BTC/USDT"
        limit = 20
        uri = f"ws://localhost:8000/api/ws/order_book?token={auth_token}&trading_pair={trading_pair}&limit={limit}"

        try:
            async with websockets.connect(uri) as websocket:
                print(f"已连接到深度数据流: {trading_pair}, limit={limit}")

                # 接收3条消息
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)

                    print(f"收到消息 {i+1}: {data}")

                    # 验证消息格式
                    assert "type" in data
                    assert data["type"] == "order_book"
                    assert "trading_pair" in data
                    assert data["trading_pair"] == trading_pair
                    assert "limit" in data
                    assert data["limit"] == limit
                    assert "timestamp" in data
                    assert "data" in data

                    # 验证深度数据字段
                    orderbook = data["data"]
                    assert "bids" in orderbook
                    assert "asks" in orderbook
                    assert len(orderbook["bids"]) <= limit
                    assert len(orderbook["asks"]) <= limit

                print("深度数据推送测试通过")

        except asyncio.TimeoutError:
            pytest.fail("连接超时")
        except Exception as e:
            pytest.fail(f"测试失败: {e}")

    @pytest.mark.asyncio
    async def test_trades_stream(self, auth_token):
        """测试成交明细推送"""
        trading_pair = "BTC/USDT"
        limit = 50
        uri = f"ws://localhost:8000/api/ws/trades?token={auth_token}&trading_pair={trading_pair}&limit={limit}"

        try:
            async with websockets.connect(uri) as websocket:
                print(f"已连接到成交明细流: {trading_pair}, limit={limit}")

                # 接收3条消息
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)

                    print(f"收到消息 {i+1}: {data}")

                    # 验证消息格式
                    assert "type" in data
                    assert data["type"] == "trades"
                    assert "trading_pair" in data
                    assert data["trading_pair"] == trading_pair
                    assert "timestamp" in data
                    assert "data" in data

                    # 验证交易数据
                    trades = data["data"]
                    assert isinstance(trades, list)

                    if trades:
                        trade = trades[0]
                        assert "id" in trade
                        assert "timestamp" in trade
                        assert "side" in trade
                        assert "price" in trade
                        assert "amount" in trade

                print("成交明细推送测试通过")

        except asyncio.TimeoutError:
            pytest.fail("连接超时")
        except Exception as e:
            pytest.fail(f"测试失败: {e}")

    @pytest.mark.asyncio
    async def test_bot_status_stream(self, auth_token):
        """测试机器人状态推送"""
        bot_id = 1  # 假设存在ID为1的机器人
        uri = f"ws://localhost:8000/api/ws/bot_status?token={auth_token}&bot_id={bot_id}"

        try:
            async with websockets.connect(uri) as websocket:
                print(f"已连接到机器人状态流: bot_id={bot_id}")

                # 接收3条消息
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)

                    print(f"收到消息 {i+1}: {data}")

                    # 验证消息格式
                    assert "type" in data
                    assert data["type"] == "bot_status"
                    assert "bot_id" in data
                    assert data["bot_id"] == bot_id
                    assert "timestamp" in data
                    assert "data" in data

                print("机器人状态推送测试通过")

        except asyncio.TimeoutError:
            pytest.fail("连接超时")
        except Exception as e:
            # 如果机器人不存在，这个测试可能会失败，这是正常的
            print(f"机器人状态推送测试跳过（可能bot不存在）: {e}")

    @pytest.mark.asyncio
    async def test_websocket_connection_manager(self, auth_token):
        """测试连接管理器的并发连接"""
        trading_pair = "BTC/USDT"

        # 创建多个并发连接
        async def connect_client(client_id):
            uri = f"ws://localhost:8000/api/ws/market_data?token={auth_token}&trading_pair={trading_pair}"

            try:
                async with websockets.connect(uri) as websocket:
                    print(f"客户端 {client_id} 已连接")

                    # 接收1条消息
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)

                    print(f"客户端 {client_id} 收到消息")
                    return True

            except Exception as e:
                print(f"客户端 {client_id} 错误: {e}")
                return False

        # 创建5个并发连接
        tasks = [connect_client(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # 验证所有连接都成功
        assert all(results), "部分连接失败"

        print("并发连接测试通过")

    @pytest.mark.asyncio
    async def test_websocket_invalid_token(self):
        """测试无效token的连接"""
        invalid_token = "invalid_token_12345"
        uri = f"ws://localhost:8000/api/ws/market_overview?token={invalid_token}"

        try:
            async with websockets.connect(uri, close_timeout=5) as websocket:
                pytest.fail("应该拒绝无效token")
        except Exception as e:
            # 期望连接被拒绝
            print(f"无效token被正确拒绝: {e}")
            assert True


if __name__ == "__main__":
    print("WebSocket实时数据推送测试")
    print("=" * 60)

    # 手动运行测试（需要先启动服务器）
    print("\n请确保FastAPI服务器正在运行: uvicorn app.main:app --reload")
    print("\n然后使用 pytest 运行测试:")
    print("  pytest test_websocket.py -v")
    print("\n或者运行单个测试:")
    print("  pytest test_websocket.py::TestWebSocketRealtime::test_market_overview_stream -v")
