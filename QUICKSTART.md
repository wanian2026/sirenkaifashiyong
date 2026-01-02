# 快速部署指南 (Mac本地)

## 快速开始 (一键启动)

```bash
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
./start.sh
```

## 手动部署步骤

### 1. 克隆仓库

```bash
git clone https://github.com/wanian2026/sirenkaifashiyong.git
cd sirenkaifashiyong
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，修改SECRET_KEY
nano .env
```

**必须修改的配置:**
```env
SECRET_KEY=your-super-secret-key-change-this
```

### 5. 初始化数据库

```bash
python init_db.py
```

### 6. 启动服务

```bash
uvicorn app.main:app --reload
```

### 7. 访问界面

打开浏览器访问: http://localhost:8000/static/index.html

**默认登录信息:**
- 用户名: `admin`
- 密码: `admin123`

## API文档访问

Swagger UI: http://localhost:8000/docs

## 停止服务

在终端按 `Ctrl+C`

## 常见问题

### Q1: Python版本问题
```bash
# 检查Python版本
python3 --version

# 需要Python 3.8或更高版本
```

### Q2: 端口被占用
```bash
# 修改.env文件中的端口
API_PORT=8001
```

### Q3: 依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 重新安装
pip install -r requirements.txt
```

### Q4: 数据库错误
```bash
# 删除旧数据库
rm crypto_bot.db

# 重新初始化
python init_db.py
```

## 下一步

1. 登录后立即修改密码
2. 阅读完整文档: [README.md](README.md)
3. 创建第一个交易机器人
4. 查看API文档了解更多功能

## 技术支持

遇到问题? 查看 [README.md](README.md) 中的故障排查部分。
