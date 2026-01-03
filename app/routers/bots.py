from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models import User, TradingBot
from app.auth import get_current_user
from app.schemas import (
    BotCreate, BotResponse, BotStatus, BotUpdate,
    RiskCheckRequest, RiskCheckResponse
)
from app.code_a_strategy import CodeAStrategy
from app.risk_management import RiskManager
from app.cache import CacheManager, CacheKey
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 缓存TTL设置（秒）
CACHE_TTL_BOTS = 30  # 机器人列表缓存30秒
CACHE_TTL_BOT_DETAIL = 60  # 机器人详情缓存60秒

# 存储运行中的机器人实例和风险管理器
running_bots = {}
bot_risk_managers = {}
cache_manager = CacheManager()


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建交易机器人"""
    new_bot = TradingBot(
        name=bot_data.name,
        exchange=bot_data.exchange,
        trading_pair=bot_data.trading_pair,
        strategy=bot_data.strategy,
        config=json.dumps(bot_data.config) if bot_data.config else None,
        user_id=current_user.id
    )

    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    return new_bot


@router.get("/", response_model=List[BotResponse])
async def get_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有机器人"""
    try:
        # 生成缓存键
        cache_key = CacheKey.user(current_user.id) + ":bots"

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"机器人列表缓存命中: user_id={current_user.id}")
            return cached_data

        # 缓存未命中，查询数据库
        bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()

        # 存入缓存
        await cache_manager.set(cache_key, bots, CACHE_TTL_BOTS)
        logger.debug(f"机器人列表已缓存: user_id={current_user.id}")

        return bots
    except Exception as e:
        logger.error(f"获取机器人列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取机器人列表失败: {str(e)}"
        )


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定机器人"""
    try:
        # 生成缓存键
        cache_key = CacheKey.bot(bot_id)

        # 尝试从缓存获取
        cached_data = await cache_manager.get(cache_key)
        if cached_data is not None:
            logger.debug(f"机器人详情缓存命中: bot_id={bot_id}")
            return cached_data

        # 缓存未命中，查询数据库
        bot = db.query(TradingBot).filter(
            TradingBot.id == bot_id,
            TradingBot.user_id == current_user.id
        ).first()

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="机器人不存在"
            )

        # 存入缓存
        await cache_manager.set(cache_key, bot, CACHE_TTL_BOT_DETAIL)
        logger.debug(f"机器人详情已缓存: bot_id={bot_id}")

        return bot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取机器人详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取机器人详情失败: {str(e)}"
        )


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_update: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新机器人配置"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    # 如果机器人在运行，不允许修改配置
    if bot.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人运行中，无法修改配置，请先停止机器人"
        )

    # 更新字段
    if bot_update.name is not None:
        bot.name = bot_update.name
    if bot_update.exchange is not None:
        bot.exchange = bot_update.exchange
    if bot_update.trading_pair is not None:
        bot.trading_pair = bot_update.trading_pair
    if bot_update.strategy is not None:
        bot.strategy = bot_update.strategy
    if bot_update.config is not None:
        bot.config = json.dumps(bot_update.config)

    db.commit()
    db.refresh(bot)

    return bot


@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动机器人"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id in running_bots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人已在运行中"
        )

    # 创建策略实例
    config = json.loads(bot.config) if bot.config else {}
    strategy = CodeAStrategy(
        trading_pair=bot.trading_pair,
        investment_amount=config.get('investment_amount', 1000),
        up_threshold=config.get('up_threshold', 0.02),
        down_threshold=config.get('down_threshold', 0.02),
        stop_loss=config.get('stop_loss', 0.10)
    )

    # 初始化策略（需要初始价格，这里先传一个示例价格，实际应从市场获取）
    # 注意：在实际运行中，应该从实时市场数据获取初始价格
    # initial_price = get_current_market_price(bot.trading_pair)
    # strategy.initialize(initial_price)
    
    # 暂时使用交易对估算初始价格
    initial_price_map = {
        'BTC/USDT': 50000,
        'ETH/USDT': 3000,
        'BNB/USDT': 400
    }
    initial_price = initial_price_map.get(bot.trading_pair, 50000)
    strategy.initialize(initial_price)

    # 初始化风险管理器
    risk_manager = RiskManager(
        max_position=config.get('max_position', 10000),
        max_daily_loss=config.get('max_daily_loss', 1000),
        max_total_loss=config.get('max_total_loss', 5000),
        max_orders=config.get('max_orders', 50),
        max_single_order=config.get('max_single_order', 1000),
        stop_loss_threshold=config.get('stop_loss_threshold', 0.05),
        take_profit_threshold=config.get('take_profit_threshold', 0.10),
        enable_auto_stop=config.get('enable_auto_stop', True)
    )

    # 存储运行中的机器人和风险管理器
    running_bots[bot_id] = strategy
    bot_risk_managers[bot_id] = risk_manager

    logger.info(f"机器人 {bot_id} 已启动，风险管理器已初始化")

    # 更新数据库状态
    bot.status = "running"
    db.commit()

    return {
        "message": "机器人已启动",
        "bot_id": bot_id,
        "risk_management": {
            "max_position": risk_manager.max_position,
            "max_daily_loss": risk_manager.max_daily_loss,
            "max_total_loss": risk_manager.max_total_loss,
            "stop_loss_threshold": risk_manager.stop_loss_threshold,
            "take_profit_threshold": risk_manager.take_profit_threshold
        }
    }


@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停止机器人"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id not in running_bots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人未运行"
        )

    # 停止策略
    running_bots[bot_id].stop()

    # 获取最终风险报告
    risk_report = None
    if bot_id in bot_risk_managers:
        risk_report = bot_risk_managers[bot_id].get_risk_report()
        logger.info(f"机器人 {bot_id} 停止时的风险报告: {risk_report}")
        del bot_risk_managers[bot_id]

    del running_bots[bot_id]

    # 更新数据库状态
    bot.status = "stopped"
    db.commit()

    response = {"message": "机器人已停止", "bot_id": bot_id}
    if risk_report:
        response["risk_report"] = risk_report

    return response


@router.get("/{bot_id}/status", response_model=BotStatus)
async def get_bot_status(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取机器人状态"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id not in running_bots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人未运行"
        )

    # 获取策略状态
    status = await running_bots[bot_id].get_strategy_status()

    return BotStatus(
        current_price=status['current_price'],
        total_invested=status['total_invested'],
        realized_profit=status['realized_profit'],
        pending_orders=status['pending_orders'],
        filled_orders=status['filled_orders']
    )


@router.post("/{bot_id}/check-risk", response_model=RiskCheckResponse)
async def check_bot_risk(
    bot_id: int,
    request: RiskCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查机器人风险限制"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人未运行，风险管理器不存在"
        )

    risk_manager = bot_risk_managers[bot_id]

    # 检查所有限制
    passed, errors = risk_manager.check_all_limits(
        position_value=request.position_value,
        order_value=request.order_value
    )

    # 获取风险报告
    risk_report = risk_manager.get_risk_report()

    # 评估风险等级
    risk_level = risk_manager.evaluate_risk_level(
        position_value=risk_report['current_position'] + request.position_value,
        unrealized_pnl=risk_report['daily_pnl']
    )

    # 根据风险等级给出建议
    if risk_level.value in ["low", "medium"]:
        recommendation = "可以继续交易"
    elif risk_level.value == "high":
        recommendation = "建议降低仓位或减少交易频率"
    else:
        recommendation = "强烈建议立即停止交易"

    return RiskCheckResponse(
        passed=passed,
        errors=errors if not passed else [],
        risk_report=risk_report,
        risk_level=risk_level.value,
        recommendation=recommendation
    )


@router.get("/{bot_id}/risk-report")
async def get_bot_risk_report(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取机器人风险报告"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
    )

    if bot_id not in bot_risk_managers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="机器人未运行，风险管理器不存在"
        )

    risk_manager = bot_risk_managers[bot_id]
    return risk_manager.get_risk_report()


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除机器人"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="机器人不存在"
        )

    if bot_id in running_bots:
        running_bots[bot_id].stop()
        del running_bots[bot_id]

    db.delete(bot)
    db.commit()

    return {"message": "机器人已删除", "bot_id": bot_id}


# ========== 批量操作 ==========

@router.post("/batch/start")
async def batch_start_bots(
    bot_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量启动机器人"""
    results = {
        "success": [],
        "failed": []
    }

    for bot_id in bot_ids:
        try:
            bot = db.query(TradingBot).filter(
                TradingBot.id == bot_id,
                TradingBot.user_id == current_user.id
            ).first()

            if not bot:
                results["failed"].append({
                    "bot_id": bot_id,
                    "reason": "机器人不存在"
                })
                continue

            if bot_id in running_bots:
                results["failed"].append({
                    "bot_id": bot_id,
                    "reason": "机器人已在运行中"
                })
                continue

            # 创建策略实例
            config = json.loads(bot.config) if bot.config else {}
            strategy = HedgeGridStrategy(
                trading_pair=bot.trading_pair,
                grid_levels=config.get('grid_levels', 10),
                grid_spacing=config.get('grid_spacing', 0.02),
                investment_amount=config.get('investment_amount', 1000),
                dynamic_grid=config.get('dynamic_grid', False),
                batch_build=config.get('batch_build', False),
                batch_count=config.get('batch_count', 3)
            )

            # 初始化网格
            await strategy.initialize_grid()

            # 初始化风险管理器
            risk_manager = RiskManager(
                max_position=config.get('max_position', 10000),
                max_daily_loss=config.get('max_daily_loss', 1000),
                max_total_loss=config.get('max_total_loss', 5000),
                max_orders=config.get('max_orders', 50),
                max_single_order=config.get('max_single_order', 1000),
                stop_loss_threshold=config.get('stop_loss_threshold', 0.05),
                take_profit_threshold=config.get('take_profit_threshold', 0.10),
                enable_auto_stop=config.get('enable_auto_stop', True)
            )

            # 存储运行中的机器人和风险管理器
            running_bots[bot_id] = strategy
            bot_risk_managers[bot_id] = risk_manager

            # 更新数据库状态
            bot.status = "running"
            db.commit()

            results["success"].append(bot_id)
            logger.info(f"批量启动: 机器人 {bot_id} 已启动")

        except Exception as e:
            results["failed"].append({
                "bot_id": bot_id,
                "reason": str(e)
            })
            logger.error(f"批量启动失败: 机器人 {bot_id}, 错误: {e}")

    return {
        "message": f"批量启动完成，成功: {len(results['success'])}，失败: {len(results['failed'])}",
        "results": results
    }


@router.post("/batch/stop")
async def batch_stop_bots(
    bot_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量停止机器人"""
    results = {
        "success": [],
        "failed": []
    }

    for bot_id in bot_ids:
        try:
            bot = db.query(TradingBot).filter(
                TradingBot.id == bot_id,
                TradingBot.user_id == current_user.id
            ).first()

            if not bot:
                results["failed"].append({
                    "bot_id": bot_id,
                    "reason": "机器人不存在"
                })
                continue

            if bot_id not in running_bots:
                results["failed"].append({
                    "bot_id": bot_id,
                    "reason": "机器人未运行"
                })
                continue

            # 停止策略
            running_bots[bot_id].stop()

            # 获取最终风险报告
            if bot_id in bot_risk_managers:
                del bot_risk_managers[bot_id]

            del running_bots[bot_id]

            # 更新数据库状态
            bot.status = "stopped"
            db.commit()

            results["success"].append(bot_id)
            logger.info(f"批量停止: 机器人 {bot_id} 已停止")

        except Exception as e:
            results["failed"].append({
                "bot_id": bot_id,
                "reason": str(e)
            })
            logger.error(f"批量停止失败: 机器人 {bot_id}, 错误: {e}")

    return {
        "message": f"批量停止完成，成功: {len(results['success'])}，失败: {len(results['failed'])}",
        "results": results
    }


@router.delete("/batch")
async def batch_delete_bots(
    bot_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量删除机器人"""
    results = {
        "success": [],
        "failed": []
    }

    for bot_id in bot_ids:
        try:
            bot = db.query(TradingBot).filter(
                TradingBot.id == bot_id,
                TradingBot.user_id == current_user.id
            ).first()

            if not bot:
                results["failed"].append({
                    "bot_id": bot_id,
                    "reason": "机器人不存在"
                })
                continue

            # 如果机器人在运行，先停止
            if bot_id in running_bots:
                running_bots[bot_id].stop()
                if bot_id in bot_risk_managers:
                    del bot_risk_managers[bot_id]
                del running_bots[bot_id]

            db.delete(bot)
            db.commit()

            results["success"].append(bot_id)
            logger.info(f"批量删除: 机器人 {bot_id} 已删除")

        except Exception as e:
            results["failed"].append({
                "bot_id": bot_id,
                "reason": str(e)
            })
            logger.error(f"批量删除失败: 机器人 {bot_id}, 错误: {e}")

    # 提交所有更改
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除提交失败: {e}")

    return {
        "message": f"批量删除完成，成功: {len(results['success'])}，失败: {len(results['failed'])}",
        "results": results
    }


@router.put("/batch/config")
async def batch_update_config(
    bot_ids: List[int],
    config_update: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量更新机器人配置"""
    results = {
        "success": [],
        "failed": []
    }

    for bot_id in bot_ids:
        try:
            bot = db.query(TradingBot).filter(
                TradingBot.id == bot_id,
                TradingBot.user_id == current_user.id
            ).first()

            if not bot:
                results["failed"].append({
                    "bot_id": bot_id,
                    "reason": "机器人不存在"
                })
                continue

            # 如果机器人在运行，不允许修改配置
            if bot.status == "running":
                results["failed"].append({
                    "bot_id": bot_id,
                    "reason": "机器人运行中，无法修改配置"
                })
                continue

            # 更新配置
            current_config = json.loads(bot.config) if bot.config else {}
            current_config.update(config_update)
            bot.config = json.dumps(current_config)

            db.commit()

            results["success"].append(bot_id)
            logger.info(f"批量配置: 机器人 {bot_id} 配置已更新")

        except Exception as e:
            results["failed"].append({
                "bot_id": bot_id,
                "reason": str(e)
            })
            logger.error(f"批量配置失败: 机器人 {bot_id}, 错误: {e}")

    return {
        "message": f"批量配置完成，成功: {len(results['success'])}，失败: {len(results['failed'])}",
        "results": results
    }


# ========== 机器人克隆 ==========

@router.post("/{bot_id}/clone", response_model=BotResponse)
async def clone_bot(
    bot_id: int,
    new_name: str = Query(..., description="新机器人名称"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """克隆机器人"""
    # 获取原机器人
    original_bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()

    if not original_bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="原机器人不存在"
        )

    # 创建新机器人
    new_bot = TradingBot(
        name=new_name,
        exchange=original_bot.exchange,
        trading_pair=original_bot.trading_pair,
        strategy=original_bot.strategy,
        config=original_bot.config,  # 复制配置
        user_id=current_user.id,
        status="stopped"  # 新机器人默认为停止状态
    )

    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    logger.info(f"机器人克隆成功: {bot_id} -> {new_bot.id}")

    return new_bot


# ========== 批量启动/停止所有机器人 ==========

@router.post("/start-all")
async def start_all_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动所有机器人"""
    try:
        # 获取用户所有停止的机器人
        bots = db.query(TradingBot).filter(
            TradingBot.user_id == current_user.id,
            TradingBot.status == "stopped"
        ).all()

        bot_ids = [bot.id for bot in bots]

        # 调用批量启动
        batch_route_result = await batch_start_bots(
            bot_ids=bot_ids,
            current_user=current_user,
            db=db
        )

        return batch_route_result

    except Exception as e:
        logger.error(f"启动所有机器人失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stop-all")
async def stop_all_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停止所有机器人"""
    try:
        # 获取用户所有运行的机器人
        bots = db.query(TradingBot).filter(
            TradingBot.user_id == current_user.id,
            TradingBot.status == "running"
        ).all()

        bot_ids = [bot.id for bot in bots]

        # 调用批量停止
        batch_route_result = await batch_stop_bots(
            bot_ids=bot_ids,
            current_user=current_user,
            db=db
        )

        return batch_route_result

    except Exception as e:
        logger.error(f"停止所有机器人失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

