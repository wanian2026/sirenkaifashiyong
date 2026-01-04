"""
风险管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import User, TradingBot
from app.auth import get_current_user, get_optional_current_user
from app.risk_management import (
    RiskManager,
    PositionRiskManager,
    calculate_position_size,
    calculate_risk_reward_ratio,
    RiskLevel
)

router = APIRouter()

# 存储每个机器人的风险管理器实例
bot_risk_managers = {}


def get_or_create_risk_manager(bot_id: int, config: dict = None) -> RiskManager:
    """获取或创建风险管理器"""
    if bot_id not in bot_risk_managers:
        risk_manager = RiskManager(
            max_position=config.get('max_position', 10000) if config else 10000,
            max_daily_loss=config.get('max_daily_loss', 1000) if config else 1000,
            max_total_loss=config.get('max_total_loss', 5000) if config else 5000,
            max_orders=config.get('max_orders', 50) if config else 50,
            max_single_order=config.get('max_single_order', 1000) if config else 1000,
            stop_loss_threshold=config.get('stop_loss_threshold', 0.05) if config else 0.05,
            take_profit_threshold=config.get('take_profit_threshold', 0.10) if config else 0.10,
            enable_auto_stop=config.get('enable_auto_stop', True) if config else True
        )
        bot_risk_managers[bot_id] = risk_manager

    return bot_risk_managers[bot_id]


@router.post("/bot/{bot_id}/check")
async def check_risk_limits(
    bot_id: int,
    position_value: float = 0,
    order_value: float = 0,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """检查机器人风险限制"""
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    # 获取或创建风险管理器
    config = {}
    if bot.config:
        import json
        config = json.loads(bot.config)

    risk_manager = get_or_create_risk_manager(bot_id, config)

    # 检查所有限制
    passed, errors = risk_manager.check_all_limits(
        position_value=position_value,
        order_value=order_value
    )

    return {
        "passed": passed,
        "errors": errors,
        "risk_report": risk_manager.get_risk_report()
    }


@router.get("/bot/{bot_id}/report")
async def get_risk_report(
    bot_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """获取风险报告"""
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
    )

    # 获取风险管理器
    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险管理器不存在，请先启动机器人"
        )

    risk_manager = bot_risk_managers[bot_id]
    return risk_manager.get_risk_report()


@router.post("/bot/{bot_id}/reset")
async def reset_daily_limits(
    bot_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """重置每日风险限制"""
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
    )

    # 获取风险管理器
    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险管理器不存在"
        )

    risk_manager = bot_risk_managers[bot_id]
    risk_manager.reset_daily_limits()

    return {"message": "每日风险限制已重置"}


@router.post("/calculate/position-size")
async def calculate_position_size_endpoint(
    account_balance: float,
    entry_price: float,
    stop_loss_price: float,
    risk_percent: float = Query(0.02, ge=0.01, le=0.1)
):
    """
    计算建议仓位大小

    Args:
        account_balance: 账户余额
        risk_percent: 风险比例（默认2%）
        entry_price: 入场价
        stop_loss_price: 止损价
    """
    position_size = calculate_position_size(
        account_balance=account_balance,
        risk_percent=risk_percent,
        entry_price=entry_price,
        stop_loss_price=stop_loss_price
    )

    position_value = position_size * entry_price
    risk_amount = account_balance * risk_percent

    return {
        "account_balance": account_balance,
        "risk_percent": risk_percent,
        "risk_amount": risk_amount,
        "entry_price": entry_price,
        "stop_loss_price": stop_loss_price,
        "position_size": position_size,
        "position_value": position_value,
        "loss_per_unit": abs(entry_price - stop_loss_price),
        "risk_reward_ratio_warning": risk_percent > 0.05  # 风险超过5%时警告
    }


@router.post("/calculate/risk-reward-ratio")
async def calculate_risk_reward_ratio_endpoint(
    entry_price: float,
    stop_loss_price: float,
    take_profit_price: float
):
    """
    计算风险收益比

    Args:
        entry_price: 入场价
        stop_loss_price: 止损价
        take_profit_price: 止盈价
    """
    ratio = calculate_risk_reward_ratio(
        entry_price=entry_price,
        stop_loss_price=stop_loss_price,
        take_profit_price=take_profit_price
    )

    risk = abs(entry_price - stop_loss_price)
    reward = abs(take_profit_price - entry_price)

    # 评估建议
    if ratio < 1:
        suggestion = "风险收益比过低，建议调整入场价或止损/止盈位"
    elif ratio < 1.5:
        suggestion = "风险收益比一般，可以接受"
    elif ratio < 2.0:
        suggestion = "风险收益比较好"
    else:
        suggestion = "风险收益比优秀"

    return {
        "entry_price": entry_price,
        "stop_loss_price": stop_loss_price,
        "take_profit_price": take_profit_price,
        "risk": risk,
        "reward": reward,
        "risk_reward_ratio": ratio,
        "suggestion": suggestion
    }


@router.post("/bot/{bot_id}/evaluate-risk")
async def evaluate_risk_level(
    bot_id: int,
    position_value: float,
    unrealized_pnl: float,
    volatility: float = 0,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """评估当前风险等级"""
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
    )

    # 获取风险管理器
    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="风险管理器不存在"
        )

    risk_manager = bot_risk_managers[bot_id]
    risk_level = risk_manager.evaluate_risk_level(
        position_value=position_value,
        unrealized_pnl=unrealized_pnl,
        volatility=volatility
    )

    # 根据风险等级给出建议
    if risk_level == RiskLevel.LOW:
        advice = "当前风险较低，可以正常交易"
    elif risk_level == RiskLevel.MEDIUM:
        advice = "当前风险中等，建议谨慎操作"
    elif risk_level == RiskLevel.HIGH:
        advice = "当前风险较高，建议降低仓位或暂停交易"
    else:
        advice = "当前风险极高，强烈建议立即停止交易"

    return {
        "risk_level": risk_level.value,
        "advice": advice,
        "position_value": position_value,
        "unrealized_pnl": unrealized_pnl,
        "volatility": volatility
    }


@router.delete("/bot/{bot_id}")
async def delete_risk_manager(
    bot_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """删除机器人风险管理器"""
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
    )

    if bot_id in bot_risk_managers:
        del bot_risk_managers[bot_id]

    return {"message": "风险管理器已删除"}

# ==================== 新增：连续亏损停止API ====================

@router.get("/bot/{bot_id}/consecutive-losses")
async def get_consecutive_losses_info(
    bot_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    获取连续亏损信息

    返回:
    - consecutive_losses: 连续亏损次数
    - consecutive_wins: 连续盈利次数
    - max_consecutive_losses: 最大允许连续亏损次数
    - recommendation: 建议
    """
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    if bot_id not in bot_risk_managers:
        return {
            "consecutive_losses": 0,
            "consecutive_wins": 0,
            "max_consecutive_losses": 5,
            "recommendation": "风险管理器未初始化"
        }

    risk_manager = bot_risk_managers[bot_id]

    return {
        "consecutive_losses": risk_manager.consecutive_losses,
        "consecutive_wins": risk_manager.consecutive_wins,
        "max_consecutive_losses": risk_manager.max_consecutive_losses,
        "should_stop": risk_manager.consecutive_losses >= risk_manager.max_consecutive_losses,
        "recommendation": "建议暂停交易" if risk_manager.consecutive_losses >= risk_manager.max_consecutive_losses else "可以继续交易"
    }


# ==================== 新增：波动率保护API ====================

@router.post("/bot/{bot_id}/update-price")
async def update_price_history(
    bot_id: int,
    symbol: str = Query(..., description="交易对，如BTC/USDT"),
    price: float = Query(..., gt=0, description="当前价格"),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    更新价格历史记录（用于波动率计算）

    Args:
        bot_id: 机器人ID
        symbol: 交易对
        price: 当前价格
    """
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="风险管理器未初始化"
        )

    risk_manager = bot_risk_managers[bot_id]
    risk_manager.update_price_history(symbol, price)

    return {"message": "价格已更新", "symbol": symbol, "price": price}


@router.get("/bot/{bot_id}/check-volatility")
async def check_volatility(
    bot_id: int,
    symbol: str = Query(..., description="交易对，如BTC/USDT"),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    检查市场波动率

    返回:
    - passed: 是否通过波动率检查
    - message: 提示信息
    - current_volatility: 当前波动率
    - volatility_threshold: 波动率阈值
    - recommendation: 建议
    """
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="风险管理器未初始化"
        )

    risk_manager = bot_risk_managers[bot_id]
    passed, message, current_volatility = risk_manager.check_volatility(symbol)

    return {
        "passed": passed,
        "message": message,
        "current_volatility": current_volatility * 100,  # 转换为百分比
        "volatility_threshold": risk_manager.volatility_threshold * 100,  # 转换为百分比
        "recommendation": "可以交易" if passed else "建议暂停交易，等待市场稳定"
    }


# ==================== 新增：异常行情检测API ====================

@router.post("/bot/{bot_id}/detect-abnormal-market")
async def detect_abnormal_market(
    bot_id: int,
    symbol: str = Query(..., description="交易对，如BTC/USDT"),
    price: float = Query(..., gt=0, description="当前价格"),
    volume: Optional[float] = Query(None, description="当前成交量"),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    检测异常行情

    返回:
    - is_abnormal: 是否异常
    - reason: 异常原因
    - price_change_percent: 价格变化百分比
    - recommendation: 建议
    """
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="风险管理器未初始化"
        )

    risk_manager = bot_risk_managers[bot_id]
    result = risk_manager.detect_abnormal_market(symbol, price, volume)

    return result


# ==================== 新增：紧急停止API ====================

@router.post("/bot/{bot_id}/emergency-stop")
async def trigger_emergency_stop(
    bot_id: int,
    reason: str = Query("用户手动触发", description="停止原因"),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    触发紧急停止

    Args:
        bot_id: 机器人ID
        reason: 停止原因
    """
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="风险管理器未初始化"
        )

    risk_manager = bot_risk_managers[bot_id]
    risk_manager.trigger_emergency_stop(reason)

    # 如果机器人正在运行，立即停止
    if bot.status == "running":
        bot.status = "stopped"
        db.commit()

    return {
        "message": "紧急停止已触发",
        "bot_id": bot_id,
        "reason": reason,
        "emergency_stop_triggered": True
    }


@router.post("/bot/{bot_id}/reset-emergency-stop")
async def reset_emergency_stop(
    bot_id: int,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    重置紧急停止状态

    允许机器人重新开始交易
    """
    # 验证机器人权限
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在或无权访问"
        )

    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="风险管理器未初始化"
        )

    risk_manager = bot_risk_managers[bot_id]
    risk_manager.reset_emergency_stop()

    return {
        "message": "紧急停止状态已重置",
        "bot_id": bot_id,
        "emergency_stop_triggered": False
    }
