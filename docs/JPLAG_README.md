# Phosphorus - JPlag Based Plagiarism Checker

基于JPlag的代码查重服务器，为Hydro提供代码抄袭检测功能。

## 功能特性

- 🔍 支持多种编程语言的代码查重
- 📊 提供详细的相似度分析报告
- 🎯 智能聚类检测抄袭集团
- 🚀 异步处理，高性能API
- 📝 完整的类型注解和文档

## 支持的编程语言

- Java
- Python 3
- C/C++
- JavaScript/TypeScript
- C#
- Go
- Kotlin
- Rust
- Scala
- Swift
- 纯文本

## 快速开始

### 环境要求

- Python 3.11+
- Java 11+ (运行JPlag需要)
- uv (Python包管理器)

### 安装依赖

```bash
# 安装项目依赖
uv sync

# 安装开发依赖
uv sync --extra dev
```

### 启动服务

```bash
# 开发模式启动
uv run python -m src.main

# 或使用脚本
uv run python run_dev.py
```

服务将在 http://localhost:8000 启动。

### API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API使用示例

### 1. 获取支持的编程语言

```bash
curl -X GET "http://localhost:8000/api/v1/jplag/languages"
```

### 2. 提交代码进行查重分析

```bash
curl -X POST "http://localhost:8000/api/v1/jplag/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@submission1.java" \
  -F "files=@submission2.java" \
  -F "files=@submission3.java" \
  -F "language=java" \
  -F "min_tokens=9" \
  -F "similarity_threshold=0.0"
```

### 3. 响应示例

```json
{
  "success": true,
  "message": "Plagiarism analysis completed successfully",
  "data": {
    "analysis_id": "uuid-here",
    "total_submissions": 3,
    "total_comparisons": 3,
    "execution_time_ms": 1500,
    "high_similarity_pairs": [
      {
        "first_submission": "submission1",
        "second_submission": "submission2",
        "similarities": {
          "AVG": 0.85,
          "MAX": 0.92
        }
      }
    ],
    "clusters": [
      {
        "index": 0,
        "average_similarity": 0.85,
        "strength": 0.90,
        "members": ["submission1", "submission2"]
      }
    ],
    "submission_stats": [
      {
        "submission_id": "submission1",
        "display_name": "submission1",
        "file_count": 1,
        "total_tokens": 245
      }
    ],
    "failed_submissions": []
  }
}
```

## 配置选项

### 环境变量

可以通过环境变量配置服务，所有变量都以 `PHOSPHORUS_` 为前缀：

```bash
# 服务配置
export PHOSPHORUS_HOST=0.0.0.0
export PHOSPHORUS_PORT=8000
export PHOSPHORUS_DEBUG=false

# JPlag配置
export PHOSPHORUS_JPLAG_JAR_PATH=lib/jplag-6.2.0.jar
export PHOSPHORUS_JPLAG_TIMEOUT=300

# 日志配置
export PHOSPHORUS_LOG_LEVEL=INFO
export PHOSPHORUS_LOG_FILE=logs/phosphorus.log
```

### 分析参数

- `language`: 编程语言 (java, python3, cpp, 等)
- `min_tokens`: 最小token匹配阈值 (1-100, 默认9)
- `similarity_threshold`: 相似度阈值 (0.0-1.0, 默认0.0)
- `base_code_included`: 是否包含基础代码模板 (默认false)
- `normalize_tokens`: 是否标准化tokens (默认false)

## 开发指南

### 项目结构

```
src/
├── api/                # API路由和模型
│   ├── health.py      # 健康检查
│   ├── jplag.py       # JPlag相关API
│   ├── models.py      # 响应模型
│   └── jplag_models.py # JPlag数据模型
├── common/            # 通用组件
│   ├── config.py      # 配置管理
│   └── logger.py      # 日志配置
├── core/              # 核心应用
│   └── app.py         # FastAPI应用工厂
├── services/          # 业务服务
│   └── jplag_service.py # JPlag服务
└── utils/             # 工具函数
    └── command.py     # 命令行工具
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_jplag_service.py -v

# 运行测试并显示覆盖率
uv run pytest --cov=src tests/
```

### 代码格式化和检查

```bash
# 格式化代码
uv run ruff format

# 检查代码质量
uv run ruff check

# 自动修复问题
uv run ruff check --fix
```

## JPlag结果解析

### 文件结构

JPlag生成的`.jplag`文件是一个ZIP压缩包，包含以下内容：

- `topComparisons.json`: 顶级比较结果
- `runInformation.json`: 运行信息和统计
- `submissionMappings.json`: 提交映射信息
- `submissionFileIndex.json`: 文件索引和token统计
- `distribution.json`: 相似度分布数据
- `cluster.json`: 聚类分析结果
- `comparisons/`: 详细比较结果目录
- `files/`: 原始提交文件副本

### 相似度指标

- `AVG`: 平均相似度
- `MAX`: 最大相似度
- `LONGEST_MATCH`: 最长匹配token数
- `MAXIMUM_LENGTH`: 最大提交长度

## 部署

### Docker部署

```dockerfile
FROM python:3.11-slim

# 安装Java (JPlag需要)
RUN apt-get update && apt-get install -y openjdk-11-jre-headless

# 复制应用
COPY . /app
WORKDIR /app

# 安装依赖
RUN pip install uv
RUN uv sync

# 启动服务
CMD ["uv", "run", "python", "-m", "src.main"]
```

### 性能考虑

1. **内存管理**: 大型提交可能消耗大量内存，建议设置适当的资源限制
2. **并发处理**: JPlag是CPU密集型任务，建议根据CPU核心数调整并发数
3. **临时文件**: 确保有足够的磁盘空间存储临时文件
4. **超时设置**: 大型分析可能需要较长时间，适当设置超时

## 许可证

本项目采用 MIT 许可证。
