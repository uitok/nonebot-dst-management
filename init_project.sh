#!/bin/bash
# 项目初始化脚本

echo "🚀 初始化 NoneBot2 DST 管理插件项目..."

# 创建目录结构
echo "📁 创建目录结构..."
mkdir -p nonebot_plugin_dst_management/{client,handlers,services,utils,models}
mkdir -p tests
mkdir -p docs
mkdir -p examples

# 创建 __init__.py 文件
echo "📝 创建 Python 包文件..."
touch nonebot_plugin_dst_management/__init__.py
touch nonebot_plugin_dst_management/client/__init__.py
touch nonebot_plugin_dst_management/handlers/__init__.py
touch nonebot_plugin_dst_management/services/__init__.py
touch nonebot_plugin_dst_management/utils/__init__.py
touch nonebot_plugin_dst_management/models/__init__.py
touch tests/__init__.py

# 创建 .gitignore
echo "📝 创建 .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# NoneBot
.env
*.db
*.log

# OS
.DS_Store
Thumbs.db

# Project specific
*.zip
*.tar.gz
EOF

# 创建 LICENSE
echo "📝 创建 MIT License..."
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 Xiao An

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# 创建示例 .env 文件
echo "📝 创建 .env.example..."
cat > .env.example << 'EOF'
# DMP API 配置
DST_API_URL=http://285k.mc5173.cn:35555
DST_API_TOKEN=your_jwt_token_here
DST_TIMEOUT=10

# 管理员配置
DST_ADMIN_USERS=["6830441855"]
DST_ADMIN_GROUPS=[]

# AI 配置（可选）
DST_ENABLE_AI=false
DST_AI_PROVIDER=openai
DST_AI_API_KEY=
DST_AI_MODEL=gpt-4
DST_AI_BASE_URL=https://api.openai.com/v1

# 日志配置
LOG_LEVEL=INFO
EOF

# 创建 CHANGELOG.md
echo "📝 创建 CHANGELOG.md..."
cat > CHANGELOG.md << 'EOF'
# 更新日志

## [Unreleased]

### 计划中
- 存档管理功能
- 模组管理功能
- AI 辅助配置

---

## [0.1.0] - 2026-02-03

### 新增
- 🎉 初始版本
- ✅ 房间管理（列表、详情、开关）
- ✅ 玩家管理（查看、踢人）
- ✅ 备份管理（列表、创建、恢复）
- ✅ 基础权限系统
- ✅ API 客户端封装

### 已知问题
- 暂不支持存档上传
- AI 功能待完善

---

## 版本说明

格式遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/)

- **主版本号**：不兼容的 API 变更
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修复
EOF

# 创建示例 bot.py
echo "📝 创建示例 bot.py..."
cat > examples/bot.py << 'EOF'
"""NoneBot2 示例 Bot - 集成 DST 管理插件"""
import nonebot
from nonebot.adapters.onebot.v11 import Adapter

# 初始化 NoneBot
nonebot.init()

# 获取 Driver
driver = get_driver()

# 配置
driver.config.host = "127.0.0.1"
driver.config.port = 8080

# 注册适配器
driver.register_adapter(Adapter)

# 加载 DST 管理插件
nonebot.load_plugin("nonebot_plugin_dst_management")

# 如果你想加载其他插件
# nonebot.load_plugin("nonebot_plugin_localstore")
# nonebot.load_plugin("nonebot_plugin_apscheduler")

if __name__ == "__main__":
    nonebot.run()
EOF

# 创建 requirements.txt
echo "📝 创建 requirements.txt..."
cat > requirements.txt << 'EOF'
# 核心依赖
nonebot2[fastapi]>=2.3.0
nonebot-adapter-onebot>=2.3.0
httpx>=0.24.0
loguru>=0.7.0
pydantic>=2.0.0

# 可选依赖
# nonebot-plugin-localstore
# nonebot-plugin-apscheduler
# openai>=1.0.0
EOF

# 创建开发环境 requirements
cat > requirements-dev.txt << 'EOF'
-r requirements.txt

# 开发依赖
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0
pre-commit>=3.3.0
EOF

# 创建 pre-commit 配置
echo "📝 创建 .pre-commit-config.yaml..."
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ["--max-line-length=100"]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
EOF

echo "✅ 项目初始化完成！"
echo ""
echo "📦 下一步："
echo "1. 创建虚拟环境: python -m venv venv"
echo "2. 激活虚拟环境: source venv/bin/activate  (Linux/Mac)"
echo "                     venv\Scripts\activate  (Windows)"
echo "3. 安装依赖: pip install -e ."
echo "4. 运行测试: pytest"
echo ""
echo "🎯 开始开发吧！"
