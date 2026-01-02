# 数据库依赖安装问题已修复

## 问题描述

在Mac上安装 `psycopg2-binary` 需要PostgreSQL开发依赖，会导致安装失败：
```
Error: pg_config executable not found.
```

## 解决方案

✅ **已修复**: 从 `requirements.txt` 中移除了 `psycopg2-binary`

项目默认使用 **SQLite** 数据库，无需任何额外依赖即可在Mac上运行。

## 立即继续安装

```bash
# 重新安装依赖（应该能成功）
pip install -r requirements.txt
```

## 数据库说明

- **默认数据库**: SQLite (`crypto_bot.db`)
- **优点**: 零配置，Mac内置，无需安装任何额外软件
- **性能**: 适合本地开发和中小规模使用

## 可选：升级到PostgreSQL

如果需要更高性能或生产环境使用，可以切换到PostgreSQL。详细步骤请参考：
- `MAC_DEPLOYMENT_GUIDE.md` 文档末尾的"配置PostgreSQL（可选）"章节

## 下一步

安装成功后，按照以下步骤继续：

```bash
# 1. 配置环境变量
cp .env.example .env
nano .env  # 修改SECRET_KEY

# 2. 初始化数据库
python init_db.py

# 3. 启动服务
./start.sh
```

---

**需要帮助？**
- 查看完整部署指南: `MAC_DEPLOYMENT_GUIDE.md`
- 查看快速指南: `QUICKSTART.md`
