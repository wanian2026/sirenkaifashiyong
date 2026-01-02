"""
风险管理增强路由
提供止损、止盈、仓位管理和风险预警的API接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.stop_loss_strategy import (
    StopLossConfig, StopLossStrategyFactory,
    FixedStopLoss, DynamicStopLoss, TrailingStopLoss, LadderStopLoss
)
from app.take_profit_strategy import (
    TakeProfitConfig, TakeProfitStrategyFactory,
    FixedTakeProfit, DynamicTakeProfit, LadderTakeProfit, PartialTakeProfit
)
from app.position_management import (
    PositionConfig, PositionManagementFactory,
    KellyCriterion, FixedRatioStrategy, ATRBasedSizing,
    RiskParityStrategy, VolatilityBasedSizing
)
from app.risk_alert import (
    RiskAlertConfig, RiskAlertStrategyFactory,
    RiskAlertManager,
    ThresholdAlert, TrendAlert, VolatilityAlert,
    DrawdownAlert, PortfolioAlert
)


router = APIRouter(prefix="/risk-enhanced", tags=["风险管理增强"])


# ============ 止损策略接口 ============

class StopLossCheckRequest(BaseModel):
    """止损检查请求"""
    strategy_type: str
    entry_price: float
    position_size: float
    current_price: float
    stop_loss_percent: Optional[float] = None
    atr: Optional[float] = None
    atr_period: Optional[int] = 14
    atr_multiplier: Optional[float] = 2.0
    trailing_percent: Optional[float] = None
    activation_profit: Optional[float] = None
    ladder_steps: Optional[List[Dict]] = None
    max_loss_amount: Optional[float] = None


@router.post("/stop-loss/calculate")
async def calculate_stop_loss(request: StopLossCheckRequest):
    """
    计算止损价格
    
    支持四种止损策略：
    - fixed: 固定百分比止损
    - dynamic: 基于ATR的动态止损
    - trailing: 追踪止损
    - ladder: 阶梯止损
    """
    try:
        config = StopLossConfig(
            strategy_type=request.strategy_type,
            entry_price=request.entry_price,
            position_size=request.position_size,
            stop_loss_percent=request.stop_loss_percent,
            atr_period=request.atr_period,
            atr_multiplier=request.atr_multiplier,
            trailing_percent=request.trailing_percent,
            activation_profit=request.activation_profit,
            ladder_steps=request.ladder_steps,
            max_loss_amount=request.max_loss_amount
        )
        
        strategy = StopLossStrategyFactory.create_strategy(config)
        stop_loss = strategy.calculate_stop_loss(request.current_price, request.atr)
        
        return {
            "success": True,
            "data": {
                "strategy_type": request.strategy_type,
                "stop_loss_price": stop_loss,
                "current_price": request.current_price,
                "distance": stop_loss - request.current_price,
                "distance_percent": (stop_loss - request.current_price) / request.current_price * 100
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop-loss/check")
async def check_stop_loss(request: StopLossCheckRequest):
    """
    检查是否触发止损
    
    返回是否应该平仓以及原因
    """
    try:
        config = StopLossConfig(
            strategy_type=request.strategy_type,
            entry_price=request.entry_price,
            position_size=request.position_size,
            stop_loss_percent=request.stop_loss_percent,
            atr_period=request.atr_period,
            atr_multiplier=request.atr_multiplier,
            trailing_percent=request.trailing_percent,
            activation_profit=request.activation_profit,
            ladder_steps=request.ladder_steps,
            max_loss_amount=request.max_loss_amount
        )
        
        strategy = StopLossStrategyFactory.create_strategy(config)
        should_close, reason = strategy.should_close_position(request.current_price, request.atr)
        
        return {
            "success": True,
            "data": {
                "should_close": should_close,
                "reason": reason,
                "current_stop_loss": strategy.current_stop_loss
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stop-loss/strategies")
async def get_stop_loss_strategies():
    """获取可用的止损策略列表"""
    return {
        "success": True,
        "data": StopLossStrategyFactory.get_available_strategies()
    }


# ============ 止盈策略接口 ============

class TakeProfitCheckRequest(BaseModel):
    """止盈检查请求"""
    strategy_type: str
    entry_price: float
    position_size: float
    current_price: float
    take_profit_percent: Optional[float] = None
    rsi: Optional[float] = None
    rsi_period: Optional[int] = 14
    rsi_overbought: Optional[float] = 70.0
    ladder_steps: Optional[List[Dict]] = None
    partial_steps: Optional[List[Dict]] = None
    max_profit_amount: Optional[float] = None
    trailing_percent: Optional[float] = None


@router.post("/take-profit/calculate")
async def calculate_take_profit(request: TakeProfitCheckRequest):
    """
    计算止盈价格
    
    支持四种止盈策略：
    - fixed: 固定百分比止盈
    - dynamic: 基于RSI和回撤的动态止盈
    - ladder: 阶梯止盈
    - partial: 部分止盈
    """
    try:
        config = TakeProfitConfig(
            strategy_type=request.strategy_type,
            entry_price=request.entry_price,
            position_size=request.position_size,
            take_profit_percent=request.take_profit_percent,
            rsi_period=request.rsi_period,
            rsi_overbought=request.rsi_overbought,
            ladder_steps=request.ladder_steps,
            partial_steps=request.partial_steps,
            max_profit_amount=request.max_profit_amount,
            trailing_percent=request.trailing_percent
        )
        
        strategy = TakeProfitStrategyFactory.create_strategy(config)
        take_profit = strategy.calculate_take_profit(request.current_price, rsi=request.rsi)
        
        return {
            "success": True,
            "data": {
                "strategy_type": request.strategy_type,
                "take_profit_price": take_profit,
                "current_price": request.current_price,
                "distance": take_profit - request.current_price,
                "distance_percent": (take_profit - request.current_price) / request.current_price * 100
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/take-profit/check")
async def check_take_profit(request: TakeProfitCheckRequest):
    """
    检查是否触发止盈
    
    返回是否应该平仓、原因以及平仓数量
    """
    try:
        config = TakeProfitConfig(
            strategy_type=request.strategy_type,
            entry_price=request.entry_price,
            position_size=request.position_size,
            take_profit_percent=request.take_profit_percent,
            rsi_period=request.rsi_period,
            rsi_overbought=request.rsi_overbought,
            ladder_steps=request.ladder_steps,
            partial_steps=request.partial_steps,
            max_profit_amount=request.max_profit_amount,
            trailing_percent=request.trailing_percent
        )
        
        strategy = TakeProfitStrategyFactory.create_strategy(config)
        should_close, reason, amount = strategy.should_close_position(request.current_price, rsi=request.rsi)
        
        return {
            "success": True,
            "data": {
                "should_close": should_close,
                "reason": reason,
                "close_amount": amount,
                "closed_amount": strategy.get_closed_amount(),
                "remaining_amount": request.position_size - strategy.get_closed_amount()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/take-profit/strategies")
async def get_take_profit_strategies():
    """获取可用的止盈策略列表"""
    return {
        "success": True,
        "data": TakeProfitStrategyFactory.get_available_strategies()
    }


# ============ 仓位管理接口 ============

class PositionCalculateRequest(BaseModel):
    """仓位计算请求"""
    strategy_type: str
    account_balance: float
    entry_price: float
    total_capital: Optional[float] = None
    stop_loss_price: Optional[float] = None
    atr: Optional[float] = None
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    kelly_fraction: Optional[float] = 0.25
    fixed_percent: Optional[float] = 0.02
    atr_multiplier: Optional[float] = 1.0
    risk_per_trade: Optional[float] = 0.02
    risk_target: Optional[float] = 0.02
    volatility_target: Optional[float] = 0.15
    position_multiplier: Optional[float] = 1.0
    max_position_size: Optional[float] = None
    min_position_size: Optional[float] = None
    max_position_percent: Optional[float] = 0.3


@router.post("/position/calculate")
async def calculate_position_size(request: PositionCalculateRequest):
    """
    计算仓位大小
    
    支持五种仓位管理策略：
    - kelly: Kelly公式
    - fixed_ratio: 固定比例
    - atr_based: 基于ATR
    - risk_parity: 风险平价
    - volatility: 基于波动率
    """
    try:
        config = PositionConfig(
            strategy_type=request.strategy_type,
            account_balance=request.account_balance,
            total_capital=request.total_capital,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            atr=request.atr,
            volatility=request.volatility,
            win_rate=request.win_rate,
            avg_win=request.avg_win,
            avg_loss=request.avg_loss,
            kelly_fraction=request.kelly_fraction,
            fixed_percent=request.fixed_percent,
            atr_multiplier=request.atr_multiplier,
            risk_per_trade=request.risk_per_trade,
            risk_target=request.risk_target,
            volatility_target=request.volatility_target,
            position_multiplier=request.position_multiplier,
            max_position_size=request.max_position_size,
            min_position_size=request.min_position_size,
            max_position_percent=request.max_position_percent
        )
        
        strategy = PositionManagementFactory.create_strategy(config)
        position_size = strategy.calculate_position_size()
        position_value = strategy.get_position_value(position_size)
        
        capital = request.total_capital or request.account_balance
        
        return {
            "success": True,
            "data": {
                "strategy_type": request.strategy_type,
                "position_size": position_size,
                "position_value": position_value,
                "position_percent": position_value / capital * 100,
                "capital": capital
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/position/strategies")
async def get_position_strategies():
    """获取可用的仓位管理策略列表"""
    return {
        "success": True,
        "data": PositionManagementFactory.get_available_strategies()
    }


# ============ 风险预警接口 ============

class RiskAlertCheckRequest(BaseModel):
    """风险预警检查请求"""
    alert_type: str
    account_balance: float
    initial_balance: Optional[float] = None
    current_price: Optional[float] = None
    prices_history: Optional[List[float]] = None
    total_position_value: Optional[float] = None
    positions: Optional[List[Dict]] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    balance_threshold: Optional[float] = None
    pnl_threshold: Optional[float] = None
    position_threshold: Optional[float] = None
    trend_period: Optional[int] = 20
    trend_threshold: Optional[float] = 0.05
    volatility_period: Optional[int] = 20
    volatility_threshold: Optional[float] = 0.05
    drawdown_threshold: Optional[float] = 0.10
    peak_balance: Optional[float] = None
    concentration_threshold: Optional[float] = 0.5
    correlation_threshold: Optional[float] = 0.8
    cooling_period: Optional[int] = 300


@router.post("/alert/check")
async def check_risk_alert(request: RiskAlertCheckRequest):
    """
    检查风险预警
    
    支持五类风险预警：
    - threshold: 阈值预警（余额、盈亏、持仓）
    - trend: 趋势预警（价格趋势、变化率）
    - volatility: 波动率预警（波动率超限、异常波动）
    - drawdown: 回撤预警（账户回撤）
    - portfolio: 组合预警（持仓集中度、持仓数量）
    """
    try:
        config = RiskAlertConfig(
            alert_type=request.alert_type,
            account_balance=request.account_balance,
            initial_balance=request.initial_balance,
            current_price=request.current_price,
            prices_history=request.prices_history,
            total_position_value=request.total_position_value,
            positions=request.positions,
            unrealized_pnl=request.unrealized_pnl,
            realized_pnl=request.realized_pnl,
            balance_threshold=request.balance_threshold,
            pnl_threshold=request.pnl_threshold,
            position_threshold=request.position_threshold,
            trend_period=request.trend_period,
            trend_threshold=request.trend_threshold,
            volatility_period=request.volatility_period,
            volatility_threshold=request.volatility_threshold,
            drawdown_threshold=request.drawdown_threshold,
            peak_balance=request.peak_balance,
            concentration_threshold=request.concentration_threshold,
            correlation_threshold=request.correlation_threshold,
            cooling_period=request.cooling_period
        )
        
        strategy = RiskAlertStrategyFactory.create_strategy(config)
        is_alert, message, details = strategy.check_alert()
        
        return {
            "success": True,
            "data": {
                "alert_type": request.alert_type,
                "is_alert": is_alert,
                "message": message,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alert/strategies")
async def get_alert_strategies():
    """获取可用的风险预警策略列表"""
    return {
        "success": True,
        "data": RiskAlertStrategyFactory.get_available_strategies()
    }


# ============ 综合风险管理接口 ============

class ComprehensiveRiskCheckRequest(BaseModel):
    """综合风险检查请求"""
    # 账户信息
    account_balance: float
    initial_balance: Optional[float] = None
    peak_balance: Optional[float] = None
    
    # 持仓信息
    positions: Optional[List[Dict]] = None
    total_position_value: Optional[float] = None
    
    # PnL信息
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    
    # 市场信息
    current_price: Optional[float] = None
    prices_history: Optional[List[float]] = None
    atr: Optional[float] = None
    volatility: Optional[float] = None
    
    # 策略配置
    stop_loss_strategy: Optional[Dict] = None
    take_profit_strategy: Optional[Dict] = None
    position_strategy: Optional[Dict] = None
    
    # 预警配置
    alert_configs: Optional[List[Dict]] = None


@router.post("/comprehensive-check")
async def comprehensive_risk_check(request: ComprehensiveRiskCheckRequest):
    """
    综合风险检查
    
    一次性检查止损、止盈、仓位和风险预警
    """
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "stop_loss": None,
            "take_profit": None,
            "position": None,
            "alerts": []
        }
        
        # 检查止损
        if request.stop_loss_strategy and request.current_price:
            sl_config = StopLossConfig(**request.stop_loss_strategy)
            sl_strategy = StopLossStrategyFactory.create_strategy(sl_config)
            should_close, reason = sl_strategy.should_close_position(
                request.current_price,
                request.atr
            )
            results["stop_loss"] = {
                "should_close": should_close,
                "reason": reason,
                "stop_loss_price": sl_strategy.current_stop_loss
            }
        
        # 检查止盈
        if request.take_profit_strategy and request.current_price:
            tp_config = TakeProfitConfig(**request.take_profit_strategy)
            tp_strategy = TakeProfitStrategyFactory.create_strategy(tp_config)
            should_close, reason, amount = tp_strategy.should_close_position(request.current_price)
            results["take_profit"] = {
                "should_close": should_close,
                "reason": reason,
                "close_amount": amount
            }
        
        # 计算仓位
        if request.position_strategy and request.current_price:
            pos_config = PositionConfig(**request.position_strategy)
            pos_strategy = PositionManagementFactory.create_strategy(pos_config)
            position_size = pos_strategy.calculate_position_size()
            results["position"] = {
                "recommended_size": position_size,
                "recommended_value": pos_strategy.get_position_value(position_size)
            }
        
        # 检查预警
        if request.alert_configs:
            for alert_config_dict in request.alert_configs:
                alert_config = RiskAlertConfig(**alert_config_dict)
                alert_strategy = RiskAlertStrategyFactory.create_strategy(alert_config)
                
                # 检查冷却期
                if alert_strategy.is_in_cooling_period():
                    continue
                
                is_alert, message, details = alert_strategy.check_alert()
                if is_alert:
                    results["alerts"].append({
                        "type": alert_config.alert_type,
                        "message": message,
                        "details": details
                    })
        
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overview")
async def risk_overview():
    """获取风险管理功能概览"""
    return {
        "success": True,
        "data": {
            "stop_loss_strategies": StopLossStrategyFactory.get_available_strategies(),
            "take_profit_strategies": TakeProfitStrategyFactory.get_available_strategies(),
            "position_strategies": PositionManagementFactory.get_available_strategies(),
            "alert_strategies": RiskAlertStrategyFactory.get_available_strategies(),
            "total_features": len(StopLossStrategyFactory.get_available_strategies()) +
                             len(TakeProfitStrategyFactory.get_available_strategies()) +
                             len(PositionManagementFactory.get_available_strategies()) +
                             len(RiskAlertStrategyFactory.get_available_strategies())
        }
    }
