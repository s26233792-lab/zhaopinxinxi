# 招聘信息爬虫+飞书自动化系统

自动从各大招聘网站爬取应届生/实习招聘信息，并实时更新到飞书多维表格。

## 功能特点

- **多数据源**: 支持应届生求职网、实习僧、牛客网、海投网等
- **高频更新**: 每3小时自动更新，确保数据及时
- **智能去重**: 基于公司名+岗位名+发布日期的三重去重机制
- **飞书集成**: 直接更新到现有飞书表格，无需手动操作
- **增量同步**: 只推送新数据，提高效率
- **Docker部署**: 一键部署到云服务器

## 快速开始

### 1. 环境要求

- Python 3.10+
- 飞书账号（用于创建多维表格）
- 云服务器（可选，用于24小时运行）

### 2. 安装依赖

```bash
# 克隆项目
git clone <repo_url>
cd recruitment_crawler

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 3. 配置飞书凭证

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入飞书凭证：

```env
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret
FEISHU_APP_TOKEN=your_app_token
FEISHU_TABLE_ID=your_table_id
LOG_LEVEL=INFO
```

#### 获取飞书凭证：

1. **App ID 和 App Secret**:
   - 访问 [飞书开放平台](https://open.feishu.cn/app)
   - 创建企业自建应用
   - 在凭证页面获取 App ID 和 App Secret

2. **App Token 和 Table ID**:
   - 打开你的飞书多维表格
   - URL 格式为: `https://xxx.feishu.cn/base/xxxxx/app/[APP_TOKEN]/table/[TABLE_ID]`
   - 从 URL 中复制对应的值

### 4. 运行

```bash
# 测试飞书连接
python main.py test

# 运行一次（测试）
python main.py run

# 启动定时任务（每3小时）
python main.py schedule
```

## Docker 部署

### 1. 构建镜像

```bash
docker-compose build
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 健康检查

访问 `http://your-server:8080/health` 查看运行状态

## 项目结构

```
recruitment_crawler/
├── config/              # 配置模块
├── crawlers/            # 爬虫模块
├── feishu/              # 飞书 API 模块
├── processors/          # 数据处理模块
├── scheduler/           # 调度模块
├── utils/               # 工具模块
├── data/                # 本地缓存
├── logs/                # 日志文件
└── main.py              # 主入口
```

## 数据字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 岗位更新 | 日期 | 信息发布/更新日期 |
| 批次 | 文本 | 招聘批次（春招、秋招等） |
| 公司名称 | 文本 | 招聘企业名称 |
| 企业类型 | 单选 | 民营/国企/央企/外企 |
| 行业 | 单选 | 互联网/金融/制造等 |
| 工作城市 | 多选 | 工作地点 |
| 岗位 | 文本 | 具体岗位名称 |
| 学历要求 | 单选 | 本科/硕士/博士 |
| 截止时间 | 日期 | 申请截止日期 |
| 招聘对象 | 多选 | 2026届/2025届/往届 |
| 免笔试 | 是/否 | 是否免除笔试 |
| 信息来源 | URL | 来源链接 |
| 内推码 | 文本 | 内推码 |

## 常见问题

### Q: 如何添加新的数据源？

在 `crawlers/` 目录下创建新的爬虫类，继承 `BaseCrawler`：

```python
from crawlers.base import BaseCrawler

class MyCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(name="mycrawler", base_url="https://example.com")

    def fetch_records(self, **kwargs):
        # 实现爬取逻辑
        pass
```

### Q: 如何修改更新频率？

修改 `config/settings.py` 中的 `SCHEDULER_INTERVAL_HOURS` 值。

### Q: 飞书表格字段不匹配怎么办？

运行 `python main.py setup` 查看现有表格的字段结构，然后修改 `config/feishu_config.py` 中的字段映射。

## 许可证

MIT License
