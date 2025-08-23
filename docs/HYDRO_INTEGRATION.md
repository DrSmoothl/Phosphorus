# Hydro OJ 集成功能

本文档描述了 Phosphorus 与 Hydro OJ 的集成功能，实现了比赛提交的自动化抄袭检测。

## 功能概述

Phosphorus 现在支持直接从 Hydro OJ 的 MongoDB 数据库中获取比赛提交记录，进行抄袭检测分析，并将结果存储回数据库。

### 核心功能

1. **比赛查重 API** - 分析比赛中所有通过的提交
2. **结果查询 API** - 获取已存储的查重结果  
3. **自动语言检测** - 支持多种编程语言
4. **MongoDB 集成** - 直接读写 Hydro 数据库

## API 接口

### 1. 比赛查重

**POST** `/api/v1/contest/plagiarism`

开始对指定比赛的所有通过提交进行抄袭检测。

#### 请求参数

```json
{
  "contest_id": "689ede86bfd7f1255f21e643",  // 比赛ID (必需)
  "min_tokens": 9,                          // 最小token匹配数 (可选, 默认9)
  "similarity_threshold": 0.0               // 相似度阈值 (可选, 默认0.0)
}
```

#### 响应示例

```json
{
  "success": true,
  "message": "Contest plagiarism check completed successfully",
  "data": {
    "analysis_id": "uuid-string",
    "contest_id": "689ede86bfd7f1255f21e643", 
    "problem_id": 2630,
    "total_submissions": 25,
    "total_comparisons": 300,
    "execution_time_ms": 5000,
    "high_similarity_pairs": [
      {
        "first_submission": "submission_21_0",
        "second_submission": "submission_22_0", 
        "similarities": {
          "AVG": 0.85,
          "MAX": 0.92
        }
      }
    ],
    "clusters": [
      {
        "index": 0,
        "average_similarity": 0.88,
        "strength": 0.75,
        "members": ["submission_21_0", "submission_22_0", "submission_23_0"]
      }
    ],
    "submission_stats": [
      {
        "submission_id": "submission_21_0",
        "display_name": "submission_21_0",
        "file_count": 1,
        "total_tokens": 45
      }
    ],
    "failed_submissions": [],
    "created_at": "2025-08-23T10:30:00Z"
  }
}
```

### 2. 查询查重结果

**GET** `/api/v1/contest/{contest_id}/plagiarism`

获取指定比赛的所有查重结果。

#### 响应示例

```json
{
  "success": true,
  "message": "Found 2 plagiarism results",
  "data": [
    {
      "analysis_id": "uuid-string-1",
      "contest_id": "689ede86bfd7f1255f21e643",
      "problem_id": 2630,
      // ... 其他字段
    },
    {
      "analysis_id": "uuid-string-2", 
      "contest_id": "689ede86bfd7f1255f21e643",
      "problem_id": 2631,
      // ... 其他字段  
    }
  ]
}
```

## 数据库结构

### Hydro 提交记录 (collection: `record`)

系统从 Hydro 的 `record` 集合中读取提交记录，筛选条件：
- `contest`: 指定的比赛ID
- `status`: 1 (Accepted) 
- `code`: 非空

### 查重结果存储 (collection: `check_plagiarism_results`)

查重结果存储在新的集合中，包含以下字段：

```javascript
{
  "_id": ObjectId,
  "contest_id": String,           // 比赛ID
  "problem_id": Number,           // 题目ID  
  "analysis_id": String,          // 分析任务ID
  "total_submissions": Number,    // 提交总数
  "total_comparisons": Number,    // 比较总数
  "execution_time_ms": Number,    // 执行时间(毫秒)
  "high_similarity_pairs": Array, // 高相似度对
  "clusters": Array,              // 聚类信息
  "submission_stats": Array,      // 提交统计
  "failed_submissions": Array,    // 失败提交
  "created_at": ISODate,          // 创建时间
  "jplag_file_path": String       // JPlag文件路径(可选)
}
```

## 支持的编程语言

系统支持以下编程语言的查重检测：

| Hydro 语言ID | JPlag 语言 | 文件扩展名 | 说明 |
|-------------|------------|------------|------|
| cc | cpp | .cpp | C++ (默认标准) |
| cc.cc98 | cpp | .cpp | C++98 标准 |
| cc.cc98o2 | cpp | .cpp | C++98 标准 (O2优化) |
| cc.cc11 | cpp | .cpp | C++11 标准 |
| cc.cc11o2 | cpp | .cpp | C++11 标准 (O2优化) |
| cc.cc14 | cpp | .cpp | C++14 标准 |
| cc.cc14o2 | cpp | .cpp | C++14 标准 (O2优化) |
| cc.cc17 | cpp | .cpp | C++17 标准 |
| cc.cc17o2 | cpp | .cpp | C++17 标准 (O2优化) |
| cc.cc20 | cpp | .cpp | C++20 标准 |
| cc.cc20o2 | cpp | .cpp | C++20 标准 (O2优化) |
| c | c | .c | C 语言 |
| pas | text | .pas | Pascal (作为文本处理) |
| java | java | .java | Java |
| kt | kotlin | .kt | Kotlin |
| kt.jvm | kotlin | .kt | Kotlin/JVM |
| py | python3 | .py | Python |
| py.py2 | python3 | .py | Python 2 |
| py.py3 | python3 | .py | Python 3 |
| py.pypy3 | python3 | .py | PyPy3 |
| php | text | .php | PHP (作为文本处理) |
| rs | rust | .rs | Rust |
| hs | text | .hs | Haskell (作为文本处理) |
| js | javascript | .js | JavaScript/Node.js |
| go | go | .go | Golang |
| rb | text | .rb | Ruby (作为文本处理) |
| cs | csharp | .cs | C# |
| bash | text | .sh | Bash (作为文本处理) |

**注意事项：**
- JPlag 原生支持的语言会进行语义级别的代码相似度检测
- 不支持的语言（标记为 text）将作为纯文本进行字符串匹配检测
- 所有 C++ 变体都映射到 JPlag 的 cpp 语言检测器
- Python 2 和 Python 3 都使用 python3 检测器进行分析

## 配置说明

### 环境变量

```bash
# MongoDB 配置
PHOSPHORUS_MONGODB_URL=mongodb://localhost:27017
PHOSPHORUS_MONGODB_DATABASE=hydro

# JPlag 配置  
PHOSPHORUS_JPLAG_JAR_PATH=lib/jplag-6.2.0.jar
PHOSPHORUS_JPLAG_TIMEOUT=300
```

### 配置文件

在 `src/common/config.py` 中可以配置：
- MongoDB 连接URL和数据库名
- JPlag JAR 文件路径
- 超时设置

## 使用示例

### 1. 使用 HTTP 客户端

```bash
# 开始查重
curl -X POST "http://localhost:8000/api/v1/contest/plagiarism" \
     -H "Content-Type: application/json" \
     -d '{"contest_id": "689ede86bfd7f1255f21e643"}'

# 查询结果
curl "http://localhost:8000/api/v1/contest/689ede86bfd7f1255f21e643/plagiarism"
```

### 2. 使用演示脚本

```bash
# 运行演示脚本（会创建测试数据）
python demo_hydro_integration.py
```

演示脚本会：
1. 创建示例比赛和提交数据
2. 执行抄袭检测
3. 显示检测结果
4. 可选择清理测试数据

## 工作流程

1. **接收请求** - API 接收比赛ID和检测参数
2. **查询提交** - 从 MongoDB 获取比赛的所有通过提交
3. **按题目分组** - 将提交按题目ID分组
4. **创建临时文件** - 为每个提交创建源代码文件
5. **执行 JPlag** - 调用 JPlag 进行相似度分析
6. **解析结果** - 解析 JPlag 输出的 .jplag 文件
7. **存储结果** - 将结构化结果存储到数据库
8. **返回响应** - 返回分析结果给客户端

## 性能考虑

- **并发处理**: 支持异步处理，可同时处理多个查重请求
- **内存管理**: 使用临时目录，分析完成后自动清理
- **批量处理**: 按题目分组，避免跨题目的无意义比较
- **最小提交数**: 每个题目至少需要2个提交才进行分析

## 错误处理

系统会处理以下错误情况：
- 比赛不存在或无提交
- 提交数量不足（每题少于2个）
- JPlag 执行失败
- 数据库连接错误
- 文件I/O错误

所有错误都会返回标准的错误响应格式：

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": { /* 详细信息 */ }
}
```

## 测试

项目包含完整的单元测试：

```bash
# 运行所有测试
uv run pytest tests/

# 运行 Hydro 相关测试
uv run pytest tests/test_hydro_*.py -v

# 运行测试并查看覆盖率
uv run pytest tests/ --cov=src --cov-report=html
```

## 部署注意事项

1. **数据库权限**: 确保应用有 Hydro 数据库的读权限和新集合的写权限
2. **JPlag 依赖**: 确保系统安装了 Java 11+ 和 JPlag JAR 文件
3. **内存资源**: 大型比赛可能需要较多内存，建议至少 2GB
4. **网络访问**: 确保应用可以访问 MongoDB 实例
5. **日志监控**: 建议配置适当的日志级别以便监控和调试

通过这个集成功能，Hydro OJ 可以方便地对比赛提交进行批量抄袭检测，提高教学和竞赛的公平性。
