# Mac 部署快速检查清单

> ✅ 完成每一步后，在方框内打勾

---

## 📋 前置检查

- [ ] Python 3.8+ 已安装
  - 检查命令：`python3 --version`

- [ ] Conda 已安装
  - 检查命令：`conda --version`
  - 如果未安装：安装 Miniforge

---

## 🚀 部署步骤

### 步骤 1：进入项目目录

- [ ] 进入项目目录
  ```bash
  cd ~/Desktop/sirenkaifashiyong
  ```

- [ ] 验证文件存在
  ```bash
  ls -la
  ```
  应该能看到：app/, workflow/, requirements.txt 等

---

### 步骤 2：创建 Conda 环境

- [ ] 创建环境
  ```bash
  conda create -n cryptobot python=3.12 -y
  ```

- [ ] 激活环境
  ```bash
  conda activate cryptobot
  ```

- [ ] 验证激活（终端显示 `(cryptobot)`）

---

### 步骤 3：安装依赖

- [ ] 运行自动安装脚本
  ```bash
  bash install_with_conda.sh
  ```

- [ ] 验证依赖安装
  ```bash
  python -c "import fastapi; print('✅')"
  python -c "import sqlalchemy; print('✅')"
  python -c "import bcrypt; print('✅')"
  python -c "import pandas; print('✅')"
  ```
  全部显示 ✅ 才算成功

---

### 步骤 4：配置环境变量

- [ ] 复制配置文件
  ```bash
  cp .env.example .env
  ```

- [ ] 生成随机密钥
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- [ ] 编辑配置文件
  ```bash
  nano .env
  ```

- [ ] 修改 SECRET_KEY（粘贴上面生成的密钥）

- [ ] 保存并退出（Ctrl+O, Enter, Ctrl+X）

---

### 步骤 5：初始化数据库

- [ ] 运行一键修复脚本
  ```bash
  bash quick_fix.sh
  ```

- [ ] 验证数据库创建成功
  ```
  创建数据库表...
  数据库表创建完成!
  默认管理员用户已创建:
  用户名: admin
  密码: admin123
  ```

---

### 步骤 6：启动服务

- [ ] 启动服务
  ```bash
  ./start.sh
  ```

- [ ] 验证服务启动成功
  ```
  INFO:     Uvicorn running on http://0.0.0.0:8000
  ```

---

### 步骤 7：访问 Web 界面

- [ ] 在浏览器打开：http://localhost:8000/static/index.html

- [ ] 登录系统
  - 用户名：`admin`
  - 密码：`admin123`

- [ ] 登录成功，看到主界面

---

## ✅ 完成验证

- [ ] Web 界面可以正常访问
- [ ] 可以正常登录
- [ ] 服务日志没有错误
- [ ] 可以创建机器人（可选）

---

## 🎉 部署完成！

恭喜！你已经成功部署了加密货币交易系统！

---

## 📝 日常使用命令

```bash
# 启动服务
cd ~/Desktop/sirenkaifashiyong
conda activate cryptobot
./start.sh

# 停止服务
Ctrl + C

# 查看日志
tail -f logs/app.log
```

---

## ❓ 遇到问题？

查看以下文档：
- `DEPLOY_STEP_BY_STEP.md` - 详细部署步骤
- `FIX_BCRYPT_ERROR.md` - bcrypt 问题
- `FIX_PANDAS_INSTALL.md` - pandas 问题
- `INIT_DB_FIX.md` - 数据库初始化问题

---

**祝你使用愉快！** 🚀
