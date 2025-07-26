# 博客文章阅读量统计系统

这是一个基于 Django + Redis 的博客文章阅读量统计系统，重点实现了缓存设计、读写分离、缓存命中率监控与数据一致性、异常分级处理和面向对象封装。

## 🎯 项目特色

- **缓存设计**: 使用Redis缓存阅读量数据，减少数据库IO操作
- **读写分离**: 读操作优先访问缓存，写操作异步更新数据库
- **缓存命中率**: 实时监控缓存命中率，提供可视化图表展示
- **异常分级处理**: 区分缓存/数据库异常级别并实现降级处理
- **面向对象封装**: 模块化设计，分离缓存操作、数据库操作和异常处理

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端页面      │    │   API接口       │    │   服务层        │
│                 │    │                 │    │                 │
│ • 文章列表      │◄──►│ • 文章统计API   │◄──►│ • 阅读统计服务  │
│ • 文章详情      │    │ • 用户统计API   │    │ • 缓存服务      │
│ • 监控仪表板    │    │ • 缓存监控API   │    │ • 异常处理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                        ┌─────────────────┐           │
                        │   Redis缓存     │◄──────────┤
                        │                 │           │
                        │ • 阅读统计缓存  │           │
                        │ • 命中率统计    │           │
                        └─────────────────┘           │
                                                       │
                        ┌─────────────────┐           │
                        │   SQLite数据库  │◄──────────┘
                        │                 │
                        │ • 文章数据      │
                        │ • 阅读统计      │
                        │ • 缓存统计      │
                        └─────────────────┘
```

## 📁 项目结构

```
workteat1/                          # 项目根目录
├── boketest/                       # Django项目主目录
│   ├── boketest/                   # 项目配置目录
│   │   ├── __init__.py
│   │   ├── settings.py             # Django配置文件（Redis配置、缓存设置）
│   │   ├── urls.py                 # 主URL配置
│   │   ├── wsgi.py                 # WSGI配置
│   │   └── asgi.py                 # ASGI配置
│   ├── blog/                       # 博客应用目录
│   │   ├── migrations/             # 数据库迁移文件
│   │   ├── services/               # 服务层目录（核心业务逻辑）
│   │   │   ├── __init__.py
│   │   │   ├── cache_service.py    # 缓存服务类（Redis操作封装）
│   │   │   ├── reading_service.py  # 阅读统计服务类（业务逻辑）
│   │   │   └── exceptions.py       # 异常处理类（分级处理机制）
│   │   ├── __init__.py
│   │   ├── models.py               # 数据模型（Article, ReadingStats, CacheHitStats）
│   │   ├── views.py                # 视图层（API接口和页面视图）
│   │   ├── urls.py                 # URL路由配置
│   │   ├── admin.py                # Django管理后台配置
│   │   ├── apps.py                 # 应用配置
│   │   └── tests.py                # 测试文件
│   ├── templates/                  # HTML模板目录
│   │   ├── base.html               # 基础模板（导航、样式、JS工具函数）
│   │   └── blog/                   # 博客模板目录
│   │       ├── article_list.html   # 文章列表页面
│   │       ├── article_detail.html # 文章详情页面（阅读统计展示）
│   │       └── dashboard.html      # 监控仪表板页面（缓存命中率图表）
│   ├── manage.py                   # Django管理脚本
│   └── db.sqlite3                  # SQLite数据库文件
├── venv/                           # Python虚拟环境
├── requirements.txt                # Python依赖包列表
├── README.md                       # 项目说明文档
├── start.bat                       # Windows启动脚本
└── setup.bat                       # Windows初始化脚本
```

### 核心文件说明

#### 🔧 服务层文件

- **`cache_service.py`** - Redis缓存服务封装
  - `CacheService`: 基础缓存操作类
  - `ReadingCacheService`: 阅读统计专用缓存服务
  - `CacheMonitorService`: 缓存监控服务

- **`reading_service.py`** - 核心业务逻辑
  - `ReadingStatsService`: 阅读统计主服务类
  - `CacheStatsService`: 缓存统计服务类

- **`exceptions.py`** - 异常处理机制
  - `ExceptionLevel`: 异常级别枚举
  - `ExceptionHandler`: 统一异常处理器
  - `FallbackStrategy`: 降级策略类

#### 📊 数据层文件

- **`models.py`** - 数据模型定义
  - `Article`: 博客文章模型
  - `ReadingStats`: 阅读统计模型
  - `CacheHitStats`: 缓存命中率统计模型

#### 🌐 视图层文件

- **`views.py`** - API接口和页面视图
  - `ArticleDetailView`: 文章详情页（含阅读记录）
  - `ArticleStatsView`: 文章统计API
  - `CacheMonitorView`: 缓存监控API
  - `DashboardView`: 仪表板视图

#### 🎨 前端文件

- **`base.html`** - 基础模板
  - Bootstrap样式框架
  - Chart.js图表库
  - 通用JavaScript工具函数

- **`article_detail.html`** - 文章详情页
  - 实时阅读统计显示
  - 用户个人阅读记录
  - AJAX刷新功能

- **`dashboard.html`** - 监控仪表板
  - 缓存命中率趋势图
  - 热门文章排行
  - 实时数据更新

#### ⚙️ 配置文件

- **`settings.py`** - Django配置
  - Redis连接配置
  - 缓存TTL设置
  - 应用注册

- **`requirements.txt`** - 依赖包
  - Django 5.2.4
  - django-redis 5.4.0
  - redis 5.0.8
  - celery 5.3.6

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Redis Server
- Django 5.2.4

### 安装步骤

1. **激活虚拟环境**:
   ```bash
   cd workteat1
   venv\Scripts\activate  # Windows
   # 或 source venv/bin/activate  # Linux/Mac
   ```

2. **安装依赖**:
   ```bash
   cd boketest
   pip install -r ../requirements.txt
   ```

3. **启动Redis服务**:
   ```bash
   # Windows (如果已安装Redis)
   redis-server
   
   # 或使用Docker
   docker run -d -p 6379:6379 redis:latest
   ```

4. **初始化数据库**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **创建管理员账户**:
   ```bash
   python manage.py createsuperuser
   ```

6. **启动开发服务器**:
   ```bash
   python manage.py runserver
   ```

### 访问系统

- **主页**: http://127.0.0.1:8000/
- **管理后台**: http://127.0.0.1:8000/admin/
- **监控仪表板**: http://127.0.0.1:8000/dashboard/

## 📱 功能介绍

### 1. 文章阅读统计

- **实时统计**: 访问文章页面时自动记录阅读量
- **多维度统计**: 
  - 总阅读次数
  - 独立用户数（登录用户）
  - 独立IP数
  - 用户个人阅读次数

### 2. 缓存策略

- **三级缓存结构**:
  - 文章总统计缓存
  - 用户阅读次数缓存
  - IP阅读次数缓存
- **缓存更新策略**: 写入时更新缓存，定期同步数据库
- **缓存失效处理**: 缓存不可用时自动降级到数据库

### 3. 监控仪表板

- **实时命中率**: 当前小时的缓存命中率
- **趋势图表**: 24小时缓存命中率趋势
- **热门文章**: 按阅读量排序的TOP5文章
- **详细统计**: 按小时统计的详细数据表格

### 4. API接口

#### 文章相关
- `GET /api/article/{id}/stats/` - 获取文章阅读统计
- `GET /api/article/{id}/user-stats/` - 获取用户阅读统计（需登录）

#### 监控相关
- `GET /api/cache-monitor/` - 获取当前缓存命中率
- `GET /api/cache-monitor/?type=daily` - 获取今日缓存统计
- `POST /api/sync-cache-stats/` - 手动同步缓存统计到数据库

#### JSON格式支持
在任何页面URL后添加 `?format=json` 可获取JSON格式数据

## 🔧 核心组件

### 1. 缓存服务 (`cache_service.py`)

```python
# 基础缓存服务
class CacheService:
    - get(key, default)      # 获取缓存
    - set(key, value, timeout) # 设置缓存
    - delete(key)            # 删除缓存
    - incr(key, amount)      # 递增操作

# 阅读统计缓存服务
class ReadingCacheService(CacheService):
    - get_article_stats()    # 获取文章统计
    - incr_user_reading_count() # 增加用户阅读次数
    - _record_cache_request() # 记录缓存请求统计
```

### 2. 统计服务 (`reading_service.py`)

```python
class ReadingStatsService:
    - record_reading()       # 记录阅读（主要业务方法）
    - get_article_stats()    # 获取文章统计（读优先缓存）
    - get_user_reading_stats() # 获取用户阅读统计
```

### 3. 异常处理 (`exceptions.py`)

```python
# 异常级别
class ExceptionLevel(Enum):
    CRITICAL = "critical"    # 严重错误
    ERROR = "error"         # 一般错误
    WARNING = "warning"     # 警告
    INFO = "info"          # 信息

# 统一异常处理器
class ExceptionHandler:
    - handle_exception()    # 统一异常处理
    
# 降级策略
class FallbackStrategy:
    - cache_fallback()      # 缓存降级
    - database_fallback()   # 数据库降级
```

## 📊 监控指标

### 缓存命中率指标

- **优秀**: ≥80% 命中率
- **良好**: 60-79% 命中率
- **需优化**: <60% 命中率

### 监控数据

- 按小时统计请求数和命中数
- 实时计算命中率百分比
- 支持数据导出和同步

## 🛠️ 开发说明

### 数据库模型

1. **Article**: 文章模型
2. **ReadingStats**: 阅读统计模型
3. **CacheHitStats**: 缓存命中率统计模型

### Redis键命名规范

- `article_stats:{article_id}` - 文章统计
- `user_reading:{article_id}:{user_id}` - 用户阅读次数
- `ip_reading:{article_id}:{ip}` - IP阅读次数
- `cache_stats:{date}:{hour}:total` - 缓存请求总数
- `cache_stats:{date}:{hour}:hits` - 缓存命中数

### 扩展建议

1. **异步处理**: 使用Celery处理数据库写入
2. **集群部署**: Redis集群 + Django多实例
3. **数据分析**: 增加更多维度的统计分析
4. **性能优化**: 批量写入、连接池优化

## 🐛 故障排除

### 常见问题

1. **Redis连接失败**:
   - 检查Redis服务是否启动
   - 确认连接配置（host, port）

2. **缓存命中率为0**:
   - 确认Redis服务正常
   - 检查缓存键是否正确设置

3. **统计数据不准确**:
   - 检查数据库同步是否正常
   - 确认缓存TTL设置

## 📄 许可证

本项目仅供学习和演示使用。

## 👥 贡献

欢迎提交Issue和Pull Request！

---

**项目作者**: Claude Sonnet and Zhao Yancheng
**创建时间**: 2025年7月
**技术栈**: Django + Redis + Bootstrap + Chart.js 