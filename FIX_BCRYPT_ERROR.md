# 修复 Bcrypt 版本兼容性问题

## 问题描述

运行 `python init_db.py` 时报错：
```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**原因**: `passlib` 和 `bcrypt` 版本不兼容。新版本的 bcrypt 移除了 `__about__` 属性，导致 passlib 无法读取版本。

---

## ✅ 已修复

我已经修改了代码，**移除 passlib 依赖**，直接使用 bcrypt。

### 修改内容

1. **更新 `app/auth.py`**
   - 移除 passlib 的 CryptContext
   - 直接使用 bcrypt 库进行密码哈希和验证

2. **更新 `requirements.txt`**
   - 移除 `passlib[bcrypt]`
   - 保留 `bcrypt==4.1.2`

---

## 📋 立即执行以下命令

### 步骤1: 重新安装依赖

```bash
# 确保在 cryptobot 环境中
conda activate cryptobot

# 卸载 passlib（如果存在）
pip uninstall passlib -y

# 安装 bcrypt（确保安装）
pip install bcrypt==4.1.2
```

### 步骤2: 删除旧数据库（如果存在）

```bash
# 删除旧的数据库文件
rm crypto_bot.db
```

### 步骤3: 重新初始化数据库

```bash
python init_db.py
```

### 预期输出

如果成功，你会看到：

```
创建数据库表...
数据库表创建完成!
默认管理员用户已创建:
用户名: admin
密码: admin123
请登录后立即修改密码!
```

---

## 🔍 验证修复

### 测试密码哈希功能

```bash
python -c "
from app.auth import get_password_hash, verify_password

# 测试密码哈希
pwd = 'test123'
hashed = get_password_hash(pwd)
print(f'密码哈希: {hashed}')

# 测试密码验证
result = verify_password(pwd, hashed)
print(f'密码验证: {\"✅ 成功\" if result else \"❌ 失败\"}')
"
```

应该输出：
```
密码哈希: $2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
密码验证: ✅ 成功
```

---

## 🎯 完整部署流程

如果数据库初始化成功，继续以下步骤：

### 步骤1: 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 生成随机密钥
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# 编辑配置文件
nano .env
```

在 `.env` 文件中粘贴生成的 SECRET_KEY。

### 步骤2: 启动服务

```bash
# 开发模式（支持热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用启动脚本
./start.sh
```

### 步骤3: 访问 Web 界面

在浏览器打开：http://localhost:8000/static/index.html

登录信息：
- 用户名: `admin`
- 密码: `admin123`

---

## 🔧 技术说明

### 为什么移除 passlib？

`passlib` 是一个密码哈希库的包装器，提供了统一的接口。但是：
- 版本更新不及时，与新版本 bcrypt 不兼容
- 增加了额外的依赖
- 对于简单的 bcrypt 使用，可以直接使用 bcrypt 库

### 直接使用 bcrypt 的优势

1. **更简单**: 直接调用 bcrypt API，无需额外抽象层
2. **更可靠**: 直接使用官方库，减少兼容性问题
3. **更轻量**: 减少依赖数量

### 密码哈希流程

```python
# 生成密码哈希
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

# 验证密码
is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

---

## ❓ 常见问题

### Q1: 仍然报错 bcrypt 模块不存在

**解决方法**:
```bash
pip install bcrypt
```

### Q2: 数据库已存在，是否需要删除？

**解决方法**:
```bash
# 删除旧数据库（建议）
rm crypto_bot.db

# 然后重新初始化
python init_db.py
```

### Q3: 登录失败

**解决方法**:
```bash
# 确保使用新数据库初始化
rm crypto_bot.db
python init_db.py

# 使用 admin / admin123 登录
```

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

访问：http://localhost:8000/static/index.html

---

## 📝 代码修改总结

### app/auth.py

**之前** (使用 passlib):
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

**现在** (直接使用 bcrypt):
```python
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
```

### requirements.txt

**之前**:
```
passlib[bcrypt]==1.7.4
```

**现在**:
```
bcrypt==4.1.2
```

---

## 🚀 下一步

数据库初始化成功后：

1. ✅ 配置 `.env` 文件
2. ✅ 启动服务: `./start.sh`
3. ✅ 访问 Web 界面
4. ✅ 创建你的第一个交易机器人

需要帮助？查看 `MAC_DEPLOYMENT_GUIDE.md` 或 `QUICKSTART.md`
