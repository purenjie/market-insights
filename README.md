# Market Insights

市场机会识别系统 - 通过 GitHub Actions 定时运行，分析市场机会并发送结果到 Telegram Bot。

## 项目特点

- **插件式架构** - 每个分析器作为独立插件，易于扩展
- **高内聚低耦合** - 模块化设计，职责清晰
- **配置驱动** - 环境变量管理敏感信息，YAML 管理业务配置
- **失败容错** - 重试机制、降级策略、详细日志
- **自动化运行** - GitHub Actions 定时任务

## 项目结构

```
market-insights/
├── config/                      # 配置文件
│   ├── analyzers.yaml          # 分析器配置
│   └── indices.yaml            # 指数列表
├── market_insights/            # 主包
│   ├── core/                   # 核心框架
│   ├── analyzers/              # 分析器插件
│   │   └── index_valuation/    # 估值分析器
│   ├── notifiers/              # 通知器插件
│   └── utils/                  # 工具模块
├── .github/workflows/          # GitHub Actions
├── requirements.txt            # 依赖
└── .env.example               # 环境变量模板
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. 本地运行

```bash
python -m market_insights
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 是 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 是 |
| `LOG_LEVEL` | 日志级别 (DEBUG/INFO/WARNING/ERROR) | 否 |
| `ENABLED_ANALYZERS` | 启用的分析器（逗号分隔） | 否 |
| `ENABLED_NOTIFIERS` | 启用的通知器（逗号分隔） | 否 |
| `MAX_RETRIES` | 最大重试次数 | 否 |
| `HTTP_TIMEOUT` | HTTP 超时时间（秒） | 否 |

### 配置文件

#### config/analyzers.yaml

```yaml
log_level: INFO
enabled_analyzers:
  - index_valuation
enabled_notifiers:
  - console
  - telegram
max_retries: 3
http_timeout: 10.0
```

#### config/indices.yaml

包含 35 个指数的配置，包括：
- 高股息指数
- 宽基指数
- 红利指数
- 现金流指数
- 行业指数

## GitHub Actions 部署

### 1. 配置 Secrets

在 GitHub 仓库设置中添加以下 Secrets：

- `TELEGRAM_BOT_TOKEN`: Telegram Bot Token
- `TELEGRAM_CHAT_ID`: Telegram Chat ID

### 2. 启用 Actions

工作流文件位于 `.github/workflows/daily-analysis.yml`

- **定时运行**: 每天 UTC 1:00 (北京时间 9:00)
- **手动触发**: 在 Actions 页面手动运行

## 功能模块

### 当前功能

#### 1. 指数估值分析 (index_valuation)

- 从红色火箭 API 获取指数数据（PE/PB/股息率）
- 计算衍生指标（隐性利率、ROE）
- 生成彩色估值表格图片
- 支持 35 个指数

### 通知渠道

- **Console**: 控制台输出（本地测试）
- **Telegram**: Telegram Bot 推送

## 扩展开发

### 添加新分析器

1. 在 `market_insights/analyzers/` 下创建新目录
2. 创建 `analyzer.py` 实现 `Analyzer` 协议
3. 创建 `config.yaml` 配置文件
4. 在 `config/analyzers.yaml` 中启用

示例结构：
```
analyzers/
└── my_analyzer/
    ├── __init__.py
    ├── analyzer.py
    ├── config.yaml
    └── models.py
```

### 添加新通知器

1. 在 `market_insights/notifiers/` 下创建新文件
2. 实现 `Notifier` 协议
3. 在 `config/analyzers.yaml` 中启用

## 技术栈

- **Python 3.11+**
- **matplotlib**: 图表生成
- **requests**: HTTP 请求
- **python-telegram-bot**: Telegram 集成
- **pyyaml**: 配置管理

## 许可证

MIT License
