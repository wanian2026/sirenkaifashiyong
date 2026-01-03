# 🚀 快速入门指南

## 5分钟快速部署

### 第一步：一键部署（1分钟）

```bash
# 进入项目目录
cd sirenkaifashiyong

# 执行一键部署脚本
bash install.sh
```

这个脚本会自动完成：
- ✅ 创建Python虚拟环境
- ✅ 安装所有依赖包
- ✅ 配置环境变量
- ✅ 初始化数据库
- ✅ 创建启动脚本

---

### 第二步：启动服务（30秒）

```bash
bash start.sh
```

看到以下信息表示启动成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

### 第三步：访问系统（10秒）

在浏览器中打开：

🌐 **Web界面**: http://localhost:8000/static/index.html

---

### 第四步：登录系统（30秒）

使用默认管理员账户登录：

👤 **用户名**: `admin`
🔑 **密码**: `admin123`

登录后立即修改密码：
1. 点击右上角头像
2. 选择"修改密码"
3. 输入新密码

---

## 📌 快速使用

### 创建第一个机器人

1. **点击"机器人管理"**
2. **点击"创建机器人"**
3. **填写基本信息**：
   - 名称：`测试机器人`
   - 交易所：`Binance`
   - 交易对：`BTC/USDT`
   - 策略：`对冲网格`
   - 投资金额：`1000`
   - 网格层数：`10`
   - 网格间距：`2%`

4. **点击"创建"**

### 启动机器人

1. **在机器人列表中找到刚创建的机器人**
2. **点击"启动"按钮**
3. **查看实时状态**

### 查看交易记录

1. **点击"交易记录"**
2. **查看所有交易历史**
3. **点击"导出"下载报表**

---

## 🛠️ 常用命令

```bash
# 停止服务
bash stop.sh

# 重启服务
bash stop.sh && bash start.sh

# 查看日志
tail -f uvicorn.log

# 进入虚拟环境
source venv/bin/activate

# 退出虚拟环境
deactivate
```

---

## 📊 主要功能

### 机器人管理
- 创建、编辑、删除机器人
- 批量启动/停止机器人
- 查看机器人实时状态

### 交易管理
- 查看交易记录
- 交易统计报表
- 导出交易数据

### 市场数据
- 实时价格监控
- K线图表
- 深度图表

### 策略系统
- 对冲网格策略
- 均值回归策略
- 动量策略

### 回测功能
- 历史数据回测
- 策略性能分析
- 参数优化

---

## 🔧 配置修改

### 修改服务端口

编辑 `.env` 文件：

```env
API_PORT=8001
```

重启服务生效：

```bash
bash stop.sh && bash start.sh
```

### 修改数据库

**使用PostgreSQL（生产环境推荐）**：

```bash
# 1. 安装PostgreSQL
brew install postgresql

# 2. 启动服务
brew services start postgresql

# 3. 创建数据库
createdb cryptobot

# 4. 修改.env
DATABASE_URL=postgresql://username:password@localhost/cryptobot

# 5. 重启服务
bash stop.sh && bash start.sh
```

### 配置交易所API

编辑 `.env` 文件：

```env
EXCHANGE_ID=binance
API_KEY=your-api-key
API_SECRET=your-api-secret
```

---

## 📖 更多资源

- **完整部署文档**: [DEPLOY_MAC.md](DEPLOY_MAC.md)
- **用户手册**: [README.md](README.md)
- **API文档**: http://localhost:8000/docs

---

## ⚠️ 安全提示

1. **立即修改默认密码**
2. **生产环境修改SECRET_KEY**
3. **保护好API密钥**
4. **定期备份数据**

---

## 🆘 遇到问题？

### 服务无法启动

```bash
# 检查端口是否被占用
lsof -i :8000

# 杀死占用进程
kill -9 <PID>
```

### 数据库初始化失败

```bash
# 删除旧数据库
rm -f crypto_bot.db

# 重新初始化
python3 init_db.py
```

### 更多问题

查看 [DEPLOY_MAC.md#常见问题](DEPLOY_MAC.md#常见问题)

---

## 🎉 开始使用

现在你已经准备好开始使用加密货币交易系统了！

**推荐阅读**:
1. [用户手册](README.md) - 了解系统功能
2. [策略说明](README.md#策略说明) - 学习交易策略
3. [API文档](http://localhost:8000/docs) - 开发集成

祝你交易愉快！🚀
