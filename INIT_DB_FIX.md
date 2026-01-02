# 修复数据库初始化问题

## 问题描述

运行 `python init_db.py` 时报错：
```
ModuleNotFoundError: No module named 'sqlalchemy'
```

**原因**: 依赖没有安装在正确的 Python 环境中。

---

## 🔍 问题分析

你的终端显示 `(venv) (base)` - 这表示两个环境同时激活，导致混乱。

我们需要：
1. **退出所有环境**
2. **使用 Conda 环境**（推荐，因为 pandas 已经通过 conda 安装）
3. **在正确环境安装依赖**

---

## ✅ 快速修复步骤

### 步骤1: 退出所有环境

```bash
# 退出 venv
deactivate

# 退出 conda base 环境（如果还在）
conda deactivate
```

现在你的终端应该不再显示 `(venv)` 或 `(base)` 前缀。

### 步骤2: 使用 Conda 安装缺失的依赖

```bash
# 安装 sqlalchemy 和其他依赖
conda install sqlalchemy -y
pip install fastapi uvicorn langgraph langchain ccxt
pip install python-jose passlib bcrypt
pip install python-multipart websockets
pip install pydantic pydantic-settings
pip install python-dotenv aiohttp jinja2
```

### 步骤3: 验证安装

```bash
# 检查 sqlalchemy 是否安装
python -c "import sqlalchemy; print('✅ sqlalchemy 版本:', sqlalchemy.__version__)"

# 检查 fastapi
python -c "import fastapi; print('✅ fastapi 版本:', fastapi.__version__)"
```

### 步骤4: 初始化数据库

```bash
python init_db.py
```

应该看到成功输出：
```
创建数据库表...
数据库表创建完成!
默认管理员用户已创建:
用户名: admin
密码: admin123
请登录后立即修改密码!
```

---

## 📋 如果仍然失败，重新创建 Conda 环境

### 步骤1: 创建新的 conda 环境

```bash
# 创建新的 conda 环境（包含 Python 3.12）
conda create -n cryptobot python=3.12 -y

# 激活新环境
conda activate cryptobot
```

现在终端应该显示 `(cryptobot)` 前缀。

### 步骤2: 安装所有依赖

```bash
# 使用 conda 安装 pandas 和 numpy
conda install pandas numpy sqlalchemy -y

# 使用 pip 安装其他依赖
pip install fastapi uvicorn langgraph langchain ccxt alembic
pip install python-jose passlib bcrypt
pip install python-multipart websockets
pip install pydantic pydantic-settings
pip install python-dotenv aiohttp jinja2
```

### 步骤3: 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置（必须修改 SECRET_KEY）
nano .env
```

生成随机密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 步骤4: 初始化数据库

```bash
python init_db.py
```

### 步骤5: 启动服务

```bash
# 开发模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或使用启动脚本：
```bash
./start.sh
```

---

## 🔍 环境检查命令

### 查看当前 Python 环境

```bash
# 查看 Python 路径
which python

# 查看 Python 版本
python --version

# 查看当前 conda 环境
conda env list
```

### 查看已安装的包

```bash
# 列出所有已安装的包
pip list

# 查找特定包
pip list | grep sqlalchemy
pip list | grep pandas
pip list | grep fastapi
```

---

## 🎯 推荐工作流程

### 永久使用 Conda 环境

```bash
# 1. 激活 cryptobot 环境
conda activate cryptobot

# 2. 进入项目目录
cd ~/Desktop/sirenkaifashiyong

# 3. 初始化数据库（只需一次）
python init_db.py

# 4. 启动服务
./start.sh

# 5. 停止服务后，下次启动只需：
# conda activate cryptobot
# cd ~/Desktop/sirenkaifashiyong
# ./start.sh
```

### 创建启动别名（可选）

在 `~/.zshrc` 文件中添加：

```bash
# 加密货币交易系统别名
alias cryptobot='cd ~/Desktop/sirenkaifashiyong && conda activate cryptobot'
alias startbot='cd ~/Desktop/sirenkaifashiyong && conda activate cryptobot && ./start.sh'
```

保存后执行：
```bash
source ~/.zshrc
```

以后只需要输入：
```bash
cryptobot   # 进入项目并激活环境
startbot    # 启动服务
```

---

## ❓ 常见问题

### Q1: conda 命令不存在

**解决方法**:
```bash
# 确保已安装 Miniforge
source ~/miniforge3/bin/activate
```

### Q2: 激活环境后 python 命令找不到

**解决方法**:
```bash
# 使用完整路径
~/miniforge3/envs/cryptobot/bin/python init_db.py
```

### Q3: pip 和 conda 安装的包冲突

**解决方法**:
```bash
# 优先使用 conda 安装数据科学包
conda install pandas numpy sqlalchemy -y

# 其他包使用 pip
pip install fastapi uvicorn ...
```

---

## 📝 完整环境配置检查清单

运行以下命令确认所有依赖已安装：

```bash
echo "=== 检查 Python 环境 ==="
which python
python --version

echo ""
echo "=== 检查核心依赖 ==="
python -c "import fastapi; print('✅ fastapi:', fastapi.__version__)"
python -c "import uvicorn; print('✅ uvicorn:', uvicorn.__version__)"
python -c "import langgraph; print('✅ langgraph:', langgraph.__version__)"
python -c "import langchain; print('✅ langchain:', langchain.__version__)"
python -c "import ccxt; print('✅ ccxt:', ccxt.__version__)"
python -c "import sqlalchemy; print('✅ sqlalchemy:', sqlalchemy.__version__)"

echo ""
echo "=== 检查数据库和认证 ==="
python -c "import alembic; print('✅ alembic:', alembic.__version__)"
python -c "import jose; print('✅ python-jobe')"

echo ""
echo "=== 检查工具包 ==="
python -c "import passlib; print('✅ passlib')"
python -c "import bcrypt; print('✅ bcrypt')"
python -c "import websockets; print('✅ websockets')"
python -c "import pydantic; print('✅ pydantic:', pydantic.__version__)"
```

如果所有检查都通过 ✅，就可以运行 `python init_db.py` 了！

---

## 🎉 成功标志

当你看到以下输出时，说明一切正常：

```
创建数据库表...
数据库表创建完成!
默认管理员用户已创建:
用户名: admin
密码: admin123
请登录后立即修改密码!
```

恭喜！现在可以启动服务了！

```bash
./start.sh
```
