# Market Insights 项目开发规范

## 项目架构原则

### 核心设计理念

1. **高内聚、低耦合**
   - 每个模块职责单一、边界清晰
   - 模块间通过接口（Protocol）通信
   - 避免循环依赖

2. **插件式架构**
   - 分析器和通知器作为独立插件
   - 通过插件加载器自动发现和加载
   - 新增功能无需修改核心代码

3. **配置驱动**
   - 环境变量管理敏感信息（Telegram Token 等）
   - YAML 文件管理业务配置（指数列表、分析器设置）
   - 配置优先级：环境变量 > YAML > 默认值

4. **无状态设计**
   - 不使用数据库
   - 所有输出为文件制品（图片、报告）
   - 适合 GitHub Actions 等无状态环境

5. **失败容错**
   - 重试机制（指数退避）
   - 降级策略（部分失败不影响整体）
   - 详细日志记录

## 代码规范

### Python 编码规范

1. **遵循 PEP 8**
   - 使用 4 空格缩进
   - 行长度不超过 88 字符（Black 标准）
   - 导入顺序：标准库 > 第三方库 > 本地模块

2. **类型提示**
   - 所有函数必须有类型提示
   - 使用 Python 3.10+ 语法（`str | None` 而非 `Optional[str]`）
   - 使用 `from __future__ import annotations` 支持前向引用

3. **文档字符串**
   - 所有公共函数、类必须有文档字符串
   - 使用 Google 风格文档字符串
   - 包含参数说明、返回值说明、异常说明

4. **注释规范**
   - 非显而易见的逻辑必须添加 `# Reason:` 注释
   - 解释"为什么"而非"是什么"
   - 中文注释用于业务逻辑，英文注释用于技术细节

### 示例代码

```python
"""模块文档字符串。

简要描述模块功能。
"""

from __future__ import annotations

from typing import Any


def fetch_data(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """从 URL 获取数据。

    Args:
        url: 数据源 URL
        timeout: 超时时间（秒）

    Returns:
        解析后的 JSON 数据

    Raises:
        DataSourceError: 请求失败时抛出
    """
    # Reason: 使用重试装饰器处理网络波动
    ...
```

## 架构模块说明

### 1. 核心框架 (core/)

- **protocols.py**: 定义所有接口（Analyzer, Notifier, DataSource）
- **config.py**: 配置管理，支持环境变量和 YAML
- **plugin_loader.py**: 插件自动发现和加载
- **orchestrator.py**: 主编排器，协调分析器和通知器
- **exceptions.py**: 自定义异常类

### 2. 分析器 (analyzers/)

每个分析器是一个独立目录，包含：
- `analyzer.py`: 主逻辑，实现 Analyzer 协议
- `models.py`: 数据模型
- `data_source.py`: 数据源客户端（可选）
- `renderer.py`: 渲染器（可选）
- `config.yaml`: 插件配置

**分析器必须实现的接口**：
```python
@property
def name(self) -> str: ...

@property
def description(self) -> str: ...

@property
def enabled(self) -> bool: ...

def analyze(self) -> AnalysisResult: ...

def validate_config(self) -> bool: ...
```

### 3. 通知器 (notifiers/)

每个通知器是一个独立文件，实现 Notifier 协议：
```python
@property
def name(self) -> str: ...

def send(self, payload: NotificationPayload) -> bool: ...

def is_available(self) -> bool: ...
```

### 4. 工具模块 (utils/)

- **retry.py**: 重试装饰器
- **logging.py**: 日志配置
- **http.py**: HTTP 工具函数

## 扩展开发指南

### 添加新分析器

1. 在 `analyzers/` 下创建新目录
2. 创建必要文件：
   ```
   my_analyzer/
   ├── __init__.py
   ├── analyzer.py      # 主逻辑
   ├── models.py        # 数据模型
   ├── config.yaml      # 配置
   └── ...              # 其他模块
   ```
3. 在 `analyzer.py` 中实现 `Analyzer` 协议
4. 在 `config/analyzers.yaml` 中启用

### 添加新通知器

1. 在 `notifiers/` 下创建新文件（如 `email.py`）
2. 实现 `Notifier` 协议
3. 在 `config/analyzers.yaml` 中启用

## 错误处理策略

### 1. 重试机制

使用 `@retry` 装饰器处理临时性失败：
```python
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def fetch_data():
    ...
```

### 2. 降级策略

部分失败不影响整体：
```python
for spec in specs:
    try:
        data = fetch_data(spec)
    except Exception as exc:
        LOG.warning("Failed to fetch %s: %s", spec, exc)
        # 使用默认值或跳过
        continue
```

### 3. 日志记录

- 使用结构化日志
- 关键操作记录 INFO 级别
- 错误使用 ERROR 级别并包含堆栈
- 调试信息使用 DEBUG 级别

## 测试规范

### 单元测试

- 使用 pytest
- 测试覆盖率 > 80%
- Mock 外部依赖（API 调用、文件 I/O）

### 集成测试

- 测试端到端流程
- 使用测试配置文件
- 验证输出文件生成

## Git 提交规范

使用 Conventional Commits：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

示例：
```
feat: add technical indicator analyzer
fix: handle missing dividend data gracefully
docs: update README with deployment guide
```

## 性能优化原则

1. **避免过早优化** - 先保证正确性
2. **使用缓存** - 避免重复计算和请求
3. **并发处理** - 数据获取可以并行
4. **资源清理** - 及时关闭文件和连接

## 安全规范

1. **敏感信息**
   - 永远不要硬编码密钥、Token
   - 使用环境变量管理
   - `.env` 文件不提交到 Git

2. **输入验证**
   - 验证所有外部输入
   - 防止注入攻击
   - 限制文件大小和数量

3. **依赖管理**
   - 定期更新依赖
   - 使用 `pip-audit` 检查漏洞
   - 锁定版本号

## 部署检查清单

### 本地测试

- [ ] 所有测试通过
- [ ] 代码格式化（Black）
- [ ] 类型检查（MyPy）
- [ ] Linter 检查（Ruff）
- [ ] 手动运行验证

### GitHub Actions

- [ ] 配置 Secrets（TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID）
- [ ] 工作流文件正确
- [ ] 手动触发测试成功
- [ ] 定时任务时间正确

## 常见问题

### Q: 如何调试分析器？

A: 使用 console 通知器本地测试：
```yaml
enabled_notifiers:
  - console
```

### Q: 如何添加新的数据源？

A: 在 `data_sources/` 下创建新文件，实现 `DataSource` 协议。

### Q: 如何修改定时任务时间？

A: 编辑 `.github/workflows/daily-analysis.yml` 中的 cron 表达式。

## 参考资源

- [PEP 8 - Python 代码风格指南](https://peps.python.org/pep-0008/)
- [PEP 544 - Protocols](https://peps.python.org/pep-0544/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [python-telegram-bot 文档](https://docs.python-telegram-bot.org/)
