# 开发者指南

本文档包含了Phosphorus项目的开发、测试和部署指南。

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Java 11+ (运行JPlag)
- uv (Python包管理器)
- Git

### 开发环境设置

```bash
# 克隆仓库
git clone <repository-url>
cd Phosphorus

# 设置开发环境
make dev-setup

# 或手动设置
uv sync --extra dev
uv run pre-commit install
```

## 🛠️ 开发工作流

### 代码质量检查

```bash
# 运行所有代码质量检查
make ci-check

# 单独运行各项检查
make format          # 代码格式化
make format-check    # 检查格式
make lint           # 代码质量检查
make lint-fix       # 自动修复lint问题
make security       # 安全检查
make test           # 运行测试
make test-cov       # 测试覆盖率
```

### Git 工作流

1. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **开发和提交**
   ```bash
   # 开发代码...
   
   # 运行pre-commit检查
   pre-commit run --all-files
   
   # 提交代码
   git add .
   git commit -m "feat: add new feature"
   ```

3. **推送和创建PR**
   ```bash
   git push origin feature/your-feature-name
   # 在GitHub上创建Pull Request
   ```

## 🧪 测试策略

### 测试类型

- **单元测试**: 测试单个函数/类
- **集成测试**: 测试组件间交互
- **API测试**: 测试HTTP端点

### 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_jplag_service.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=html

# 运行特定标记的测试
pytest tests/ -m "not slow"
```

### 编写测试

```python
# test_example.py
import pytest
from src.services.example_service import ExampleService

class TestExampleService:
    """测试示例服务"""
    
    def test_example_function(self):
        """测试示例函数"""
        service = ExampleService()
        result = service.example_function("input")
        assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """测试异步函数"""
        service = ExampleService()
        result = await service.async_function()
        assert result is not None
```

## 📋 代码规范

### Python代码风格

- 遵循PEP 8
- 使用Ruff进行格式化和Lint
- 行长度限制为88字符
- 使用类型注解

### 文档字符串

使用Google风格的文档字符串：

```python
def example_function(param1: str, param2: int) -> bool:
    """示例函数说明。
    
    Args:
        param1: 第一个参数的说明
        param2: 第二个参数的说明
        
    Returns:
        返回值的说明
        
    Raises:
        ValueError: 当参数无效时抛出
    """
    pass
```

### 提交信息规范

使用[Conventional Commits](https://www.conventionalcommits.org/)格式：

- `feat: 新功能`
- `fix: 修复bug`
- `docs: 文档更新`
- `style: 代码格式调整`
- `refactor: 代码重构`
- `test: 测试相关`
- `chore: 构建/工具相关`

## 🔧 工具配置

### IDE设置

#### VS Code

推荐安装的扩展：
- Python
- Pylance
- Ruff
- GitLens
- Python Test Explorer

推荐的settings.json配置：
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "none",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### Pre-commit Hooks

已配置的hooks：
- 代码格式检查
- YAML语法检查
- 大文件检查
- 合并冲突检查
- Ruff格式化和Lint
- MyPy类型检查
- Bandit安全检查

## 🚀 部署

### Docker部署

```bash
# 构建镜像
docker build -t phosphorus:latest .

# 运行容器
docker run -p 8000:8000 phosphorus:latest

# 或使用make命令
make docker-build
make docker-run
```

### 环境变量

```bash
# 服务配置
PHOSPHORUS_HOST=0.0.0.0
PHOSPHORUS_PORT=8000
PHOSPHORUS_DEBUG=false

# JPlag配置
PHOSPHORUS_JPLAG_JAR_PATH=lib/jplag-6.2.0.jar
PHOSPHORUS_JPLAG_TIMEOUT=300

# 日志配置
PHOSPHORUS_LOG_LEVEL=INFO
PHOSPHORUS_LOG_FILE=logs/phosphorus.log
```

## 🔍 调试指南

### 本地调试

```bash
# 启动开发服务器
make run-dev

# 或直接运行
uv run python run_dev.py
```

### 日志查看

```python
from src.common import get_logger

logger = get_logger()
logger.info("调试信息")
logger.error("错误信息")
```

### 性能分析

```bash
# 安装性能分析工具
uv add --dev py-spy

# 分析运行中的进程
py-spy record -o profile.svg -- python -m src.main
```

## 📊 监控和指标

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/api/health
```

### 性能指标

- 响应时间
- 内存使用
- CPU使用率
- JPlag执行时间

## 🔒 安全最佳实践

1. **代码安全**
   - 运行Bandit安全扫描
   - 检查依赖漏洞
   - 避免硬编码敏感信息

2. **API安全**
   - 输入验证
   - 速率限制
   - 错误信息不泄露敏感信息

3. **部署安全**
   - 使用非root用户
   - 最小权限原则
   - 定期更新依赖

## 📝 故障排除

### 常见问题

1. **JPlag执行失败**
   - 检查Java版本
   - 确认JPlag JAR文件存在
   - 检查文件权限

2. **测试失败**
   - 确认所有依赖已安装
   - 检查环境变量设置
   - 查看详细错误信息

3. **导入错误**
   - 检查PYTHONPATH设置
   - 确认模块结构正确
   - 重新安装依赖

### 获取帮助

- 查看项目文档
- 检查GitHub Issues
- 联系维护者

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 运行所有检查
5. 提交Pull Request
6. 等待代码审查

感谢你的贡献！
