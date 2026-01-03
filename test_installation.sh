#!/bin/bash

echo "🧪 测试依赖安装..."

# 测试关键依赖是否安装成功
echo "1️⃣ 测试 FastAPI..."
python -c "import fastapi; print(f'✅ FastAPI {fastapi.__version__}')"

echo "2️⃣ 测试 SQLAlchemy..."
python -c "import sqlalchemy; print(f'✅ SQLAlchemy {sqlalchemy.__version__}')"

echo "3️⃣ 测试 Pydantic..."
python -c "import pydantic; print(f'✅ Pydantic {pydantic.__version__}')"

echo "4️⃣ 测试 ccxt..."
python -c "import ccxt; print(f'✅ ccxt {ccxt.__version__}')"

echo "5️⃣ 测试 pandas..."
python -c "import pandas; print(f'✅ pandas {pandas.__version__}')"

echo "6️⃣ 测试 coincurve（如果已安装）..."
if python -c "import coincurve" 2>/dev/null; then
    python -c "import coincurve; print(f'✅ coincurve {coincurve.__version__}')"
else
    echo "⚠️  coincurve 未安装（如果项目不需要可以忽略）"
fi

echo "7️⃣ 测试项目核心模块..."
python -c "from app.code_a_strategy import CodeAStrategy; print('✅ CodeAStrategy 导入成功')"

echo "✅ 所有测试完成！"
