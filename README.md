# 加密货币交易系统

基于LangGraph工作流的加密货币合约交易系统，支持对冲网格策略和Web界面操作。

## 🚀 快速开始

### Mac本地部署

**一键部署（推荐）:**

```bash
# 1. 进入项目目录
cd sirenkaifashiyong

# 2. 一键部署
bash install.sh

# 3. 启动服务
bash start.sh
```

**5分钟快速入门**: [查看 QUICKSTART.md](QUICKSTART.md)

**详细部署文档**: [查看 DEPLOY_MAC.md](DEPLOY_MAC.md)

## 功能特性

- 🤖 **多交易所支持**: 支持Binance、OKX、Huobi等主流交易所
- 📊 **对冲网格策略**: 智能网格交易，自动低买高卖
- 🔐 **安全认证**: JWT用户认证，保护账户安全
- 📈 **实时监控**: WebSocket实时推送市场数据和交易状态
- 💾 **数据库持久化**: 支持SQLite和PostgreSQL数据库
- 🌐 **Web界面**: 直观的管理界面，轻松管理交易机器人

## 技术栈

- **后端框架**: FastAPI
- **工作流引擎**: LangGraph
- **交易所API**: CCXT
- **数据库ORM**: SQLAlchemy
- **数据库**: PostgreSQL/SQLite
- **认证**: JWT
- **实时通信**: WebSocket

## Mac本地部署指南

### 1. 克隆GitHub仓库

```bash
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
```

### 2. 创建Python虚拟环境

```bash
# 确保系统已安装Python 3.8+
python3 --version

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，配置必要的参数
# 必须修改SECRET_KEY为一个安全的随机字符串
nano .env
```

**重要配置项说明:**

```env
# 数据库配置 (默认使用SQLite)
DATABASE_URL=sqlite:///./crypto_bot.db

# 如果要使用PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost/cryptobot

# JWT密钥 (必须修改为随机字符串!)
SECRET_KEY=your-super-secret-key-here-change-it-in-production

# API服务配置
API_HOST=0.0.0.0
API_PORT=8000

# 交易所API配置 (可选，用于实盘交易)
EXCHANGE_ID=binance
API_KEY=your-api-key
API_SECRET=your-api-secret
```

### 5. 初始化数据库

```bash
python init_db.py
```

这将创建所有必要的数据库表，并创建默认管理员账户:
- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **安全提示**: 登录后请立即修改默认密码!

### 6. 启动服务

```bash
# 开发模式 (支持热重载)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. 访问Web界面

启动服务后，在浏览器中访问:

- **Web界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 使用说明

### 首次登录

1. 打开 http://localhost:8000/static/index.html
2. 使用默认账户登录:
   - 用户名: `admin`
   - 密码: `admin123`

### 创建交易机器人

1. 点击"机器人管理" → "创建机器人"
2. 填写机器人配置:
   - 机器人名称
   - 交易所选择
   - 交易对 (如 BTC/USDT)
   - 策略类型 (对冲网格策略)
   - 投资金额
   - 网格层数 (建议10-20)
   - 网格间距 (建议1-3%)

3. 点击"创建"按钮

### 启动和停止机器人

- **启动机器人**: 点击机器人卡片上的"启动"按钮
- **停止机器人**: 点击机器人卡片上的"停止"按钮
- **查看状态**: 点击"状态"按钮查看实时交易数据

### 查看交易记录

- 点击"交易记录"查看所有交易历史
- 点击"仪表盘"查看统计数据和市场数据

## API接口说明

### 认证接口

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### 机器人接口

- `POST /api/bots` - 创建机器人
- `GET /api/bots` - 获取机器人列表
- `GET /api/bots/{id}` - 获取指定机器人
- `POST /api/bots/{id}/start` - 启动机器人
- `POST /api/bots/{id}/stop` - 停止机器人
- `GET /api/bots/{id}/status` - 获取机器人状态
- `DELETE /api/bots/{id}` - 删除机器人

### 交易记录接口

- `GET /api/trades/bot/{id}` - 获取指定机器人的交易记录
- `GET /api/trades/recent` - 获取最近的交易记录
- `GET /api/trades/stats` - 获取交易统计

## 策略说明

### 对冲网格策略

对冲网格策略是一种低风险的量化交易策略:

1. **网格设置**: 在指定价格区间内设置多个买卖订单
2. **自动执行**: 价格触及网格线时自动执行交易
3. **对冲机制**: 买入后自动在更高价位设置卖出订单
4. **风险控制**: 内置风险检查机制，控制仓位和风险敞口

**优势:**
- ✅ 适合横盘震荡市场
- ✅ 自动化程度高
- ✅ 风险可控
- ✅ 不需要持续盯盘

**适用场景:**
- 交易量大的主流币种
- 价格波动相对稳定的市场
- 中长期持有策略

## 注意事项

### 安全建议

1. **修改默认密码**: 首次登录后立即修改admin密码
2. **保护SECRET_KEY**: 不要将.env文件提交到版本控制
3. **API密钥安全**: 实盘交易时使用只读或有限权限的API密钥
4. **防火墙设置**: 生产环境建议配置防火墙

### 实盘交易

如果要进行实盘交易:

1. **获取交易所API密钥**:
   - 登录交易所网站
   - 在API管理页面创建新密钥
   - 建议限制IP白名单和权限

2. **配置.env文件**:
   ```env
   API_KEY=your-exchange-api-key
   API_SECRET=your-exchange-api-secret
   ```

3. **小资金测试**:
   - 先用小额资金测试
   - 验证策略效果
   - 观察运行状态

### 模拟交易

默认使用模拟模式，无需API密钥即可测试:

```env
# 不配置API_KEY和API_SECRET，系统将自动使用模拟模式
```

## 故障排查

### 常见问题

**1. 数据库连接失败**
```bash
# 检查数据库文件是否存在
ls -la crypto_bot.db

# 重新初始化数据库
python init_db.py
```

**2. 端口被占用**
```bash
# 修改.env中的端口
API_PORT=8001
```

**3. 依赖安装失败**
```bash
# 升级pip
pip install --upgrade pip

# 单独安装失败的包
pip install package_name
```

**4. WebSocket连接失败**
- 确保服务正在运行
- 检查浏览器控制台错误信息
- 验证API_PORT配置

## 性能优化

### 生产环境建议

1. **使用PostgreSQL**: SQLite适合开发，生产环境建议使用PostgreSQL
2. **多worker部署**: 使用4-8个worker提高并发处理能力
3. **Nginx反向代理**: 使用Nginx作为反向代理，提高性能和安全性
4. **启用缓存**: 使用Redis缓存频繁访问的数据
5. **日志管理**: 配置日志轮转，避免日志文件过大

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/sirenkaifashiyong/static;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 开发指南

### 项目结构

```
sirenkaifashiyong/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI主程序
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models.py            # 数据库模型
│   ├── schemas.py           # Pydantic模型
│   ├── auth.py              # 认证模块
│   ├── strategies.py        # 交易策略
│   ├── websocket.py         # WebSocket服务
│   └── routers/
│       ├── __init__.py
│       ├── auth.py          # 认证路由
│       ├── bots.py          # 机器人路由
│       └── trades.py        # 交易记录路由
├── workflow/
│   ├── __init__.py
│   ├── state.py             # 工作流状态定义
│   ├── nodes.py             # 工作流节点
│   └── graph.py             # 工作流图
├── static/
│   └── index.html           # Web前端界面
├── init_db.py               # 数据库初始化脚本
├── requirements.txt         # Python依赖
├── .env.example             # 环境变量示例
├── .gitignore              # Git忽略文件
└── README.md               # 项目文档
```

### 添加新的交易策略

1. 在`app/strategies.py`中实现策略类
2. 在`workflow/nodes.py`中添加策略节点
3. 在`workflow/graph.py`中更新工作流图
4. 在前端添加策略选择选项

### 扩展交易所支持

当前支持Binance、OKX、Huobi，添加新交易所:

1. 检查CCXT是否支持该交易所
2. 在.env中添加交易所配置
3. 在前端添加交易所选项

## 许可证

本项目仅供学习和研究使用。实盘交易风险自担。

## 免责声明

- 加密货币交易存在高风险，可能导致资金损失
- 本系统不提供任何投资建议
- 使用本系统进行实盘交易前请充分了解风险
- 作者不对任何交易损失负责

## 技术支持

如有问题或建议，请通过以下方式联系:

- GitHub Issues: https://github.com/wanian2026/sirenkaifashiyong/issues

## 更新日志

### v1.0.0 (2024-01-01)

- ✨ 初始版本发布
- ✨ 支持对冲网格策略
- ✨ Web界面实现
- ✨ WebSocket实时推送
- ✨ 多交易所支持
- ✨ JWT认证系统
