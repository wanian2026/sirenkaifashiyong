#!/bin/bash
# 安全推送脚本 - 分批提交新功能

echo "=== 开始安全推送流程 ==="

# 第1批：核心功能模块
echo "📦 提交第1批：核心功能模块"
git add app/backtest.py app/cache.py app/database_optimization.py app/notifications.py app/rbac.py app/risk_management.py app/exchange.py
git commit -m "feat: 添加核心功能模块

- 回测引擎：支持历史数据回测
- Redis缓存：提升查询性能
- 数据库优化：索引和查询优化
- 通知系统：多渠道通知支持
- RBAC权限：角色权限管理
- 风险管理：实时风险监控
- 交易所接口：统一的交易所API"

# 第2批：API路由
echo "📦 提交第2批：API路由"
git add app/routers/backtest.py app/routers/notifications.py app/routers/optimization.py app/routers/orders.py app/routers/rbac.py app/routers/risk.py
git commit -m "feat: 添加新功能API路由

- 回测API：策略回测接口
- 通知API：通知管理接口
- 优化API：系统优化接口
- 订单API：订单管理接口
- 权限API：权限管理接口
- 风控API：风险管理接口"

# 第3批：前端界面
echo "📦 提交第3批：前端界面"
git add static/dashboard.html
git commit -m "feat: 添加可视化仪表盘

- 响应式设计
- 4种图表类型（K线、盈亏、策略对比、性能监控）
- 实时数据更新
- 暗色主题"

# 第4批：文档
echo "📦 提交第4批：项目文档"
git add docs/ CHECKLIST.md DEPLOY_STEP_BY_STEP.md FEATURES.md FEATURES_COMPLETED.md NOW_START_HERE.md
git commit -m "docs: 完善项目文档

- API文档
- 部署检查清单
- 部署步骤指南
- 功能说明文档
- 快速开始指南"

# 第5批：现有模块增强
echo "📦 提交第5批：现有模块增强"
git add app/main.py app/routers/auth.py app/routers/bots.py app/routers/trades.py app/schemas.py app/strategies.py app/websocket.py
git commit -m "refactor: 增强现有模块功能

- 注册新API路由
- 增强认证模块
- 完善机器人管理
- 优化交易记录
- 扩展数据模型
- 增强策略功能
- 优化WebSocket通信"

# 推送到远程
echo "🚀 推送到GitHub"
git push origin main

echo "=== 推送完成 ==="
