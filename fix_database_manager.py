#!/usr/bin/env python3
"""
修复database_manager.py中的权限检查问题
"""

import re

# 读取文件
with open("app/routers/database_manager.py", "r", encoding="utf-8") as f:
    content = f.read()

# 定义需要修复的模式和对应的正确代码
fixes = [
    (
        r"    # 检查权限\n    # Permission check\n        # Get user permissions\n        if not PermissionChecker\.has_permission\(user_permissions, Permission\.SYSTEM_BACKUP\):",
        "    # 检查权限\n    user_permissions = get_user_permissions(current_user)\n    if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_BACKUP):"
    ),
    (
        r"    # 检查权限\n    # Permission check\n        # Get user permissions\n        if not PermissionChecker\.has_permission\(user_permissions, Permission\.SYSTEM_OPTIMIZE\):",
        "    # 检查权限\n    user_permissions = get_user_permissions(current_user)\n    if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_OPTIMIZE):"
    ),
    (
        r"    # 检查权限\n    # Permission check\n        # Get user permissions\n        if not PermissionChecker\.has_permission\(user_permissions, Permission\.SYSTEM_ANALYZE\):",
        "    # 检查权限\n    user_permissions = get_user_permissions(current_user)\n    if not PermissionChecker.has_permission(user_permissions, Permission.SYSTEM_ANALYZE):"
    )
]

# 应用修复
for pattern, replacement in fixes:
    content = re.sub(pattern, replacement, content)

# 保存文件
with open("app/routers/database_manager.py", "w", encoding="utf-8") as f:
    f.write(content)

print("修复完成！")
