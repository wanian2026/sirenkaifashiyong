# Python 版本清理指南

## 📋 查看已安装的 Python 版本

### 1. 查看系统 Python
```bash
# 查看 Python 3 版本
python3 --version

# 查看 Python 路径
which python3

# 查看所有 Python 3.x 版本
ls -la /usr/bin/python*
ls -la /opt/homebrew/bin/python*
```

### 2. 查看 Homebrew 安装的 Python
```bash
# 列出所有通过 Homebrew 安装的 Python
brew list | grep python

# 查看特定版本的详细信息
brew info python@3.14
brew info python@3.13
```

### 3. 使用清理脚本
```bash
# 运行清理检查脚本
chmod +x cleanup_python.sh
./cleanup_python.sh
```

---

## 🗑️ 删除不需要的 Python 版本

### ⚠️ 重要警告
- **不要删除系统自带的 Python**（位于 `/usr/bin/`）
- **只能删除通过 Homebrew 安装的 Python**（位于 `/opt/homebrew/bin/` 或 `/usr/local/bin/`）
- **删除前请确认不再使用该版本**

### 方法 1：使用交互式删除脚本（推荐）
```bash
# 运行交互式删除脚本
chmod +x delete_python_interactive.sh
./delete_python_interactive.sh
```

### 方法 2：手动删除（高级用户）
```bash
# 删除 Python 3.13（示例）
brew uninstall python@3.13

# 删除 Python 3.11
brew uninstall python@3.11

# 删除多个版本
brew uninstall python@3.11 python@3.10 python@3.9
```

### 方法 3：删除所有旧版本（保留当前版本）
```bash
# 假设你想保留 Python 3.14，删除其他版本
brew uninstall python@3.13 python@3.12 python@3.11 python@3.10

# 清理缓存
brew cleanup --prune=all
```

---

## 🧹 清理虚拟环境

### 查找所有虚拟环境
```bash
# 查找项目目录下的虚拟环境
find ~ -type d -name "venv" -o -name ".venv" 2>/dev/null | head -20

# 查找所有虚拟环境（可能需要很长时间）
find ~ -type d -name "env" 2>/dev/null | head -20
```

### 删除不需要的虚拟环境
```bash
# 删除当前项目的虚拟环境
rm -rf venv

# 删除其他虚拟环境
rm -rf path/to/venv
rm -rf path/to/.venv

# 批量删除（谨慎使用）
# rm -rf ~/Documents/*/venv
```

---

## 🧹 清理 pip 缓存

### 查看缓存大小
```bash
# 查看 pip 缓存目录
ls -lh ~/.cache/pip

# 查看缓存大小
du -sh ~/.cache/pip
```

### 清理缓存
```bash
# 清理所有 pip 缓存
pip cache purge

# 或者使用特定 Python 版本清理
python3 -m pip cache purge
```

---

## 🧹 清理 Homebrew

### 清理旧版本
```bash
# 清理所有旧版本
brew cleanup --prune=all

# 清理特定软件的旧版本
brew cleanup python@3.13

# 查看 Homebrew 占用空间
du -sh /opt/homebrew
```

### 查看可清理的空间
```bash
# 查看可清理的空间
brew cleanup -n

# 查看特定包的可清理空间
brew cleanup -n python@3.13
```

---

## 🔄 重新创建虚拟环境

### 使用当前 Python 版本
```bash
# 激活新的虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 使用特定 Python 版本
```bash
# 使用 Python 3.12 创建虚拟环境
python3.12 -m venv venv312
source venv312/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 📊 检查 Python 使用情况

### 查看哪些包依赖 Python
```bash
# 查看依赖特定 Python 版本的包
brew deps python@3.14

# 查看所有依赖关系
brew deps --installed | grep python
```

### 检查虚拟环境的 Python 版本
```bash
# 检查虚拟环境使用的 Python 版本
venv/bin/python --version

# 列出虚拟环境中安装的包
venv/bin/pip list
```

---

## 🚨 常见问题

### Q1: 如何知道哪些项目使用了特定 Python 版本？
```bash
# 搜索项目中的 .python-version 文件
find ~ -name ".python-version" -exec echo {} \; -exec cat {} \;

# 搜索项目中的 venv
find ~ -type d -name "venv" -exec sh -c 'echo "{}"; {}/bin/python --version 2>/dev/null' \;
```

### Q2: 删除 Python 后如何恢复？
```bash
# 重新安装特定版本
brew install python@3.13

# 设置为默认版本（可选）
brew link python@3.13
```

### Q3: 如何设置默认 Python 版本？
```bash
# 方法 1: 使用 brew link
brew unlink python@3.14
brew link python@3.13

# 方法 2: 修改 PATH
echo 'export PATH="/opt/homebrew/opt/python@3.13/bin:$PATH"' >> ~/.zshrc

# 方法 3: 使用 pyenv（推荐多版本管理）
brew install pyenv
pyenv global 3.13.0
```

### Q4: 删除后命令报错怎么办？
```bash
# 更新 shell 配置
source ~/.zshrc
# 或
source ~/.bash_profile

# 重新加载环境变量
exec $SHELL
```

---

## 📝 推荐清理流程

### 步骤 1: 检查当前状态
```bash
# 运行检查脚本
./cleanup_python.sh

# 记录当前使用的版本
python3 --version > ~/current_python_version.txt
```

### 步骤 2: 删除不需要的 Python
```bash
# 使用交互式脚本
./delete_python_interactive.sh

# 或手动删除
brew uninstall python@3.13 python@3.11
```

### 步骤 3: 清理缓存
```bash
# 清理 pip 缓存
pip cache purge

# 清理 Homebrew 缓存
brew cleanup --prune=all
```

### 步骤 4: 删除旧虚拟环境
```bash
# 删除不需要的虚拟环境
rm -rf venv_old
rm -rf venv_python313
```

### 步骤 5: 重新创建虚拟环境
```bash
# 使用当前 Python 创建新的虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt
```

### 步骤 6: 验证
```bash
# 检查 Python 版本
python --version

# 检查虚拟环境
which python

# 运行测试
./test_installation.sh
```

---

## ⚠️ 安全建议

1. **不要删除系统自带的 Python**
   - 系统自带 Python 位于 `/usr/bin/`
   - 删除可能导致系统功能异常

2. **保留当前项目使用的版本**
   - 确认项目依赖的 Python 版本
   - 删除前备份虚拟环境

3. **逐个删除并测试**
   - 不要一次性删除多个版本
   - 每次删除后测试其他项目是否正常

4. **使用虚拟环境管理器**
   - 推荐 pyenv 管理 Python 版本
   - 推荐 venv 管理项目依赖

---

## 🛠️ 高级工具

### pyenv（Python 版本管理器）
```bash
# 安装 pyenv
brew install pyenv

# 列出所有可用版本
pyenv install -l

# 安装特定版本
pyenv install 3.13.0

# 设置全局默认版本
pyenv global 3.13.0

# 设置项目特定版本
cd ~/project
pyenv local 3.12.0
```

### conda（Anaconda/Miniconda）
```bash
# 列出所有环境
conda env list

# 删除环境
conda env remove --name myenv

# 清理缓存
conda clean --all
```

---

## 📞 获取帮助

如果遇到问题：
1. 查看清理脚本日志
2. 检查 Homebrew 文档
3. 查看 Python 官方文档

---

## ✅ 总结

- **查看**: 使用 `cleanup_python.sh` 检查状态
- **删除**: 使用 `delete_python_interactive.sh` 安全删除
- **清理**: 清理 pip 缓存和 Homebrew 缓存
- **验证**: 重新创建虚拟环境并测试

记住：**宁可保留多个版本，也不要误删重要版本！**
