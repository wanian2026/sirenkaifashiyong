# 本地MacBook登录问题排查指南

## 问题现象

所有登录测试都返回401 Unauthorized错误。

## 可能的原因

1. **本地数据库不同**：本地MacBook的数据库与远程服务器数据库不同
2. **Admin用户未正确初始化**：admin用户可能不存在或密码不匹配
3. **浏览器请求格式问题**：前端发送的请求格式可能仍有问题

---

## 排查步骤

### 步骤1：测试新的简化登录页面

创建了一个简化的登录测试页面，使用最基本的请求格式。

在浏览器中打开：
```
http://localhost:8000/static/simple_login_test.html
```

操作：
1. 点击"测试登录"按钮
2. 打开浏览器控制台（按F12）
3. 切换到Console标签
4. 查看详细的请求和响应信息
5. 切换到Network标签
6. 找到`/api/auth/login`请求
7. 查看请求头和请求体
8. 查看响应状态和响应体

**请截图发送给我，特别是：**
- Console标签中的日志输出
- Network标签中请求的详细信息

---

### 步骤2：检查本地数据库

在终端中运行以下命令：

```bash
python scripts/check_local_db.py
```

预期输出（如果一切正常）：
```
============================================================
  Admin用户信息
============================================================
用户ID: 1
用户名: admin
邮箱: admin@example.com
角色: admin
是否激活: True
邮箱已验证: False
MFA已启用: False
创建时间: 2026-01-03 04:20:58
密码哈希: $2b$12$L6X/t/JlmXypgfU/4P3JHeCGOAtbQ8o5kSZKLX0ddZQ...
============================================================

测试密码: admin123
验证结果: ✅ 密码正确
```

**可能的输出：**

1. **Admin用户不存在**
   ```
   ❌ Admin用户不存在

   请运行以下命令创建admin用户：
     python scripts/init_db.py
   ```

   解决方法：运行 `python scripts/init_db.py`

2. **密码错误**
   ```
   验证结果: ❌ 密码错误

   建议：重新初始化数据库
     python scripts/init_db.py
   ```

   解决方法：运行 `python scripts/init_db.py`

---

### 步骤3：重新初始化数据库（如果需要）

如果步骤2显示需要重新初始化，运行：

```bash
python scripts/init_db.py
```

预期输出：
```
============================================================
  数据库初始化脚本
============================================================

正在创建数据库表...
✅ 数据库表创建完成

✅ 默认管理员用户创建成功
   用户名: admin
   密码: admin123
   邮箱: admin@example.com

============================================================
  初始化完成！
============================================================
```

---

### 步骤4：重新测试登录

数据库初始化完成后：

1. 刷新浏览器中的登录测试页面
2. 使用默认账号：
   - 用户名：`admin`
   - 密码：`admin123`
3. 点击"测试登录"按钮
4. 查看结果

---

## 其他测试方法

### 使用curl命令测试

在终端中运行：

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -v
```

预期返回：
```
< HTTP/1.1 200 OK
< content-type: application/json
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}
```

如果curl可以成功，但浏览器不行，说明问题出在前端请求格式上。

---

## 常见问题

### Q1: 401错误但是数据库检查正常

**可能原因**：浏览器请求格式问题

**检查方法**：
1. 打开浏览器控制台（F12）
2. 切换到Network标签
3. 找到`/api/auth/login`请求
4. 查看Request Headers：
   - Content-Type应该是 `application/x-www-form-urlencoded`
   - 不应该有 `multipart/form-data`
5. 查看Request Payload：
   - 格式应该是 `username=admin&password=admin123`
   - 不应该是FormData或其他格式

**解决方法**：
- 使用简化测试页面 `simple_login_test.html`
- 检查浏览器控制台的请求详情
- 截图发送给我进一步分析

---

### Q2: 数据库文件在哪里？

默认情况下，SQLite数据库文件位于项目根目录：
```
crypto_bot.db
```

如果配置了不同的DATABASE_URL，请检查 `.env` 文件或 `app/config.py`。

---

### Q3: 如何删除数据库并重新创建？

```bash
# 删除数据库文件
rm crypto_bot.db

# 重新初始化
python scripts/init_db.py
```

⚠️ **注意**：这会删除所有数据！

---

### Q4: 修改admin密码

如果需要修改admin密码，可以运行：

```python
# 在Python REPL中
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == "admin").first()
admin.hashed_password = get_password_hash("your_new_password")
db.commit()
db.close()
```

---

## 需要反馈的信息

如果按照上述步骤操作后仍有问题，请提供：

1. **浏览器控制台截图**：
   - Console标签中的日志
   - Network标签中请求的详细信息

2. **数据库检查脚本的输出**：
   ```bash
   python scripts/check_local_db.py
   ```

3. **curl测试结果**：
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
   ```

4. **后端日志**：
   - 查看终端中uvicorn的日志输出
   - 特别是登录请求的日志

---

## 更新日志

### 2026-01-04
- 创建简化登录测试页面
- 创建本地数据库检查脚本
- 添加详细的排查指南
