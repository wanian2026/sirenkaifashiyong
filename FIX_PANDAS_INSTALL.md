# Pandas 安装问题修复指南

## 问题描述

在 Mac 上安装 pandas 失败，错误信息：
```
error: metadata-generation-failed
× Encountered error while generating package metadata.
╰─> pandas
```

**原因**: Python 3.14 版本太新，pandas 还没有完全支持。

---

## 🔧 解决方案（按推荐顺序）

### ✅ 方法1: 使用 Conda（强烈推荐）

Conda 会自动处理依赖兼容性问题。

#### 步骤1: 安装 Miniforge

Miniforge 是轻量级的 conda 发行版，支持 Apple Silicon（M1/M2/M3）。

```bash
# 下载并安装 Miniforge（适用于 Apple Silicon）
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh

# 或者 Intel Mac 使用：
# curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh

# 安装
bash Miniforge3-MacOSX-arm64.sh
```

按提示操作（按 Enter 确认，输入 yes 同意协议等）

安装完成后，重启终端。

#### 步骤2: 使用 Conda 安装依赖

```bash
# 进入项目目录
cd sirenkaifashiyong

# 使用 conda 安装 pandas 和 numpy
conda install pandas numpy -y

# 使用 pip 安装其他依赖
pip install fastapi uvicorn langgraph langchain
pip install ccxt sqlalchemy alembic
pip install python-jose passlib bcrypt
pip install python-multipart websockets
pip install pydantic pydantic-settings
pip install python-dotenv aiohttp jinja2
```

#### 步骤3: 继续部署

```bash
# 配置环境变量
cp .env.example .env
nano .env  # 修改 SECRET_KEY

# 初始化数据库
python init_db.py

# 启动服务
./start.sh
```

---

### ✅ 方法2: 使用 Homebrew 降级 Python 版本

如果你不想使用 conda，可以降级到 Python 3.11 或 3.12。

#### 步骤1: 安装 Python 3.12

```bash
# 使用 Homebrew 安装 Python 3.12
brew install python@3.12

# 验证安装
python3.12 --version
```

#### 步骤2: 重新创建虚拟环境

```bash
# 进入项目目录
cd sirenkaifashiyong

# 删除旧虚拟环境
rm -rf venv

# 使用 Python 3.12 创建虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证 Python 版本
python --version
# 应该显示 Python 3.12.x
```

#### 步骤3: 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装所有依赖
pip install -r requirements.txt
```

#### 步骤4: 继续部署

```bash
# 配置环境变量
cp .env.example .env
nano .env  # 修改 SECRET_KEY

# 初始化数据库
python init_db.py

# 启动服务
./start.sh
```

---

### ✅ 方法3: 使用预编译 Wheel

如果必须使用 Python 3.14，可以尝试安装预编译的 wheel。

#### 步骤1: 安装构建工具

```bash
# 安装 Xcode 命令行工具
xcode-select --install
```

在弹出的对话框中点击"安装"。

#### 步骤2: 使用 pip 安装 pandas（带特定选项）

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装构建工具
pip install Cython wheel

# 尝试安装 pandas（使用无二进制模式）
pip install --no-binary :all: pandas
```

⚠️ **警告**: 这个方法需要很长时间编译，可能仍然失败。

---

## 🎯 推荐选择

| 方法 | 难度 | 成功率 | 推荐指数 |
|------|------|--------|----------|
| 方法1: Conda | ⭐ 简单 | ✅ 99% | ⭐⭐⭐⭐⭐ |
| 方法2: 降级Python | ⭐⭐ 中等 | ✅ 95% | ⭐⭐⭐⭐ |
| 方法3: 预编译Wheel | ⭐⭐⭐⭐ 困难 | ⚠️ 50% | ⭐⭐ |

**强烈推荐使用方法1（Conda）！**

---

## 📝 方法1（Conda）详细步骤

### 1. 下载 Miniforge

打开终端，执行：

```bash
# Apple Silicon (M1/M2/M3)
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh

# Intel Mac
# curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh
```

### 2. 安装 Miniforge

```bash
# 运行安装脚本
bash Miniforge3-MacOSX-arm64.sh
```

安装过程：
- 按 Enter 阅读 License
- 输入 `yes` 同意
- 按 Enter 确认默认安装路径
- 输入 `yes` 初始化 conda

### 3. 重启终端

关闭并重新打开终端窗口。

### 4. 进入项目目录

```bash
cd sirenkaifashiyong
```

### 5. 安装依赖

```bash
# 使用 conda 安装 pandas 和 numpy（关键步骤）
conda install pandas numpy -y

# 使用 pip 安装其他依赖
pip install fastapi uvicorn langgraph langchain ccxt
pip install sqlalchemy alembic python-jose passlib bcrypt
pip install python-multipart websockets pydantic pydantic-settings
pip install python-dotenv aiohttp jinja2
```

### 6. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 生成随机密钥
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# 编辑配置文件
nano .env
```

在 `.env` 文件中：
- 粘贴上面生成的 SECRET_KEY
- 其他配置保持默认

### 7. 初始化数据库

```bash
python init_db.py
```

### 8. 启动服务

```bash
./start.sh
```

访问 http://localhost:8000/static/index.html

---

## 🔍 验证安装

安装完成后，验证 pandas 是否正常：

```bash
python -c "import pandas; print(pandas.__version__)"
```

应该输出类似：`2.2.4`

---

## ❓ 常见问题

### Q1: Conda 安装后找不到 conda 命令

**解决方法**:
```bash
# 重启终端
# 或者手动初始化
source ~/miniforge3/bin/activate
```

### Q2: Conda 安装很慢

**解决方法**:
```bash
# 使用镜像源
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes
```

### Q3: 仍然安装失败

**解决方法**:
```bash
# 清理缓存
conda clean --all
pip cache purge

# 重新尝试
conda install pandas numpy -y
```

---

## 🎉 成功标志

如果看到以下输出，说明安装成功：

```bash
$ python -c "import pandas; print(pandas.__version__)"
2.2.4
```

继续执行部署步骤即可！

---

## 📞 需要帮助？

- 推荐使用方法1（Conda），成功率最高
- 遇到问题请查看 `MAC_DEPLOYMENT_GUIDE.md`
