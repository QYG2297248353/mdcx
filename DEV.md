# MDCx 开发文档

## 环境准备

### 1. 安装 Python 环境

推荐使用 Miniconda 管理 Python 版本：

```powershell
conda create -n mdcx python=3.13
conda activate mdcx
```

### 2. 安装 uv

```powershell
pip install uv
```

### 3. 安装 pnpm

```powershell
npm install -g pnpm
# 或启用 corepack
corepack enable
```

### 4. 克隆仓库并安装依赖

```powershell
git clone https://github.com/sqzw-x/mdcx.git
cd mdcx

# 安装 Python 依赖（含 Web 可选依赖和开发依赖）
uv sync --all-extras --dev

# 安装前端依赖
cd ui
pnpm install
cd ..

# 安装 pre-commit 钩子
uv run pre-commit install
```

### 5. IDE 配置

推荐使用 VS Code 打开 `mdcx.code-workspace` 工作区文件，已预配置 Python 和前端相关设置。

---

## 目录结构

```
mdcx/
├── main.py                # Qt 桌面版入口
├── server.py              # FastAPI Web 服务入口
├── pyproject.toml         # Python 项目配置（uv 包管理）
├── uv.lock                # uv 依赖锁文件
├── ruff.toml              # Ruff 代码检查与格式化配置
├── mdcx/                  # Python 源代码
│   ├── __init__.py
│   ├── consts.py          # 运行时常量（版本号、路径、平台标识）
│   ├── signals.py         # 信号抽象层（Qt 信号 / Server 信号）
│   ├── crawler.py         # 爬虫提供者（注册与路由）
│   ├── browser.py         # 浏览器实例管理（Playwright/Patchright）
│   ├── web_async.py       # 异步 HTTP 客户端封装
│   ├── image.py           # 图片处理（裁剪、缩放、水印）
│   ├── number.py          # 番号解析与识别
│   ├── manual.py          # 手动配置映射表
│   ├── llm.py             # LLM 接口封装
│   ├── base/              # 基础功能模块
│   │   ├── file.py        # 文件扫描、整理、清理
│   │   ├── image.py       # 图片处理流程
│   │   ├── number.py      # 番号提取逻辑
│   │   ├── translate.py   # 翻译基础逻辑
│   │   ├── video.py       # 视频处理（截图、BIF、预览）
│   │   ├── web.py         # 网络下载（封面、预告片等）
│   │   └── web_sync.py    # 同步网络请求
│   ├── cmd/               # CLI 命令
│   │   ├── crawl.py       # crawl 命令：爬虫调试工具
│   │   └── gen_enums.py   # gen_enums 命令：生成枚举代码
│   ├── config/            # 配置管理模块
│   │   ├── models.py      # Pydantic 配置模型定义
│   │   ├── manager.py     # ConfigManager 单例，加载/保存 JSON 配置
│   │   ├── enums.py       # 配置枚举定义
│   │   ├── computed.py    # 计算属性（派生配置）
│   │   ├── extend.py      # 配置扩展函数
│   │   ├── resources.py   # 资源路径管理
│   │   ├── ui_schema.py   # JSON Schema 生成（供 WebUI 表单用）
│   │   └── v1.py          # V1 旧版配置兼容迁移
│   ├── core/              # 核心刮削工作流
│   │   ├── scraper.py     # 主刮削流程（扫描→番号→爬取→翻译→下载→NFO→整理）
│   │   ├── file.py        # 文件创建、移动、命名
│   │   ├── file_crawler.py # 单文件爬取流程
│   │   ├── image.py       # 图片加水印
│   │   ├── nfo.py         # NFO 元数据生成与写入
│   │   ├── translate.py   # 标题/演员翻译
│   │   ├── web.py         # 网络资源下载
│   │   └── utils.py       # 刮削工具函数
│   ├── crawlers/          # 各网站爬虫（约 40 个）
│   │   ├── __init__.py    # 爬虫注册与工厂函数
│   │   ├── base/          # 爬虫基类
│   │   │   ├── base.py    # GenericBaseCrawler 抽象基类
│   │   │   ├── parser.py  # HTML 解析器基类
│   │   │   ├── compat.py  # 旧版爬虫兼容适配
│   │   │   └── types.py   # 爬虫上下文类型
│   │   ├── javbus.py      # 各网站爬虫实现
│   │   ├── javlibrary.py
│   │   ├── fc2.py
│   │   ├── ...            # 约 40 个网站爬虫
│   │   └── dmm_new/       # DMM 多子站爬虫模块
│   ├── controllers/       # Qt UI 控制器
│   │   ├── main_window/   # 主窗口控制
│   │   │   ├── init.py    # UI 初始化（信号绑定）
│   │   │   ├── handlers.py    # 事件处理函数
│   │   │   ├── main_window.py # 主窗口类
│   │   │   ├── load_config.py # 配置 → UI 加载
│   │   │   ├── save_config.py # UI → 配置保存
│   │   │   ├── bind_utils.py  # 控件绑定工具
│   │   │   └── style.py       # 样式设置
│   │   └── cut_window.py      # 图片裁剪窗口
│   ├── views/             # Qt Designer UI 文件
│   │   ├── MDCx.ui        # 主窗口 UI（Qt Designer 编辑）
│   │   ├── MDCx.py        # UI 编译后的 Python 代码
│   │   ├── posterCutTool.ui   # 裁剪工具 UI
│   │   ├── posterCutTool.py   # 裁剪工具编译代码
│   │   └── CustomClass.py     # 自定义 Qt 控件
│   ├── server/            # FastAPI Web 服务
│   │   ├── api/v1/        # REST API 路由
│   │   │   ├── __init__.py    # 路由聚合
│   │   │   ├── config.py      # 配置相关 API
│   │   │   ├── files.py       # 文件浏览 API
│   │   │   ├── legacy.py      # 旧版兼容 API
│   │   │   ├── utils.py       # API 工具函数
│   │   │   └── ws.py          # WebSocket 推送
│   │   ├── ws/            # WebSocket 管理
│   │   │   ├── auth.py        # WS 认证中间件
│   │   │   ├── manager.py     # WS 连接管理
│   │   │   └── types.py       # WS 消息类型
│   │   ├── config.py      # 服务配置
│   │   ├── dependencies.py    # FastAPI 依赖注入
│   │   ├── signals.py     # Server 信号实现
│   │   └── var.py         # 服务全局变量
│   ├── tools/             # 独立工具模块
│   │   ├── emby_actor_image.py  # Emby 演员图更新
│   │   ├── emby_actor_info.py   # Kodi/Emby 演员信息
│   │   ├── actress_db.py        # 演员数据库管理
│   │   ├── missing.py           # 缺失文件检测
│   │   ├── subtitle.py          # 字幕处理
│   │   └── wiki.py              # Wiki 相关工具
│   ├── models/            # 业务数据模型
│   │   ├── types.py       # 核心数据类型
│   │   ├── enums.py       # 业务枚举
│   │   ├── flags.py       # 状态标志位
│   │   ├── emby.py        # Emby 相关模型
│   │   └── log_buffer.py  # 日志缓冲
│   ├── utils/             # 工具函数
│   │   ├── __init__.py
│   │   ├── file.py        # 文件操作工具
│   │   ├── path.py        # 路径工具
│   │   ├── video.py       # 视频工具
│   │   ├── language.py    # 语言工具
│   │   ├── gather_group.py # 并发分组工具
│   │   └── dataclass.py   # 数据类工具
│   └── gen/               # 自动生成的代码
│       └── field_enums.py # 字段枚举自动生成
├── scripts/               # 开发/构建脚本
│   ├── build.py           # PyInstaller 打包脚本
│   ├── bump.py            # 版本号管理
│   ├── changelog.py       # 变更日志生成
│   ├── extract.py         # 资源提取
│   ├── filter_map_xml.py  # 映射表过滤
│   ├── pyuic.sh           # Qt UI → Python 代码生成
│   └── get-dev-info.sh    # 开发环境信息收集
├── tests/                 # 测试
│   ├── crawlers/          # 爬虫测试
│   │   ├── conftest.py
│   │   ├── test_crawler.py
│   │   ├── test_parsers.py
│   │   └── parser.py
│   ├── test_config_conversion.py
│   ├── test_path.py
│   ├── test_ui_schema.py
│   ├── test_utils.py
│   └── test_video.py
├── ui/                    # WebUI 前端
│   ├── src/
│   │   ├── App.tsx        # 应用入口
│   │   ├── index.tsx      # 渲染入口
│   │   ├── routes/        # 页面路由（TanStack Router）
│   │   │   ├── __root.tsx     # 根路由布局
│   │   │   ├── index.tsx      # 首页（刮削）
│   │   │   ├── settings.tsx   # 设置页
│   │   │   ├── logs.tsx       # 日志页
│   │   │   ├── tool.tsx       # 工具页
│   │   │   ├── about.tsx      # 关于页
│   │   │   ├── auth.tsx       # 认证设置
│   │   │   └── network.tsx    # 网络设置
│   │   ├── components/    # UI 组件
│   │   │   ├── Layout.tsx     # 页面布局
│   │   │   ├── FileBrowser.tsx # 文件浏览器
│   │   │   ├── WebSocketStatus.tsx # WS 状态指示
│   │   │   └── form/          # 自定义表单字段
│   │   ├── client/        # OpenAPI 自动生成的 HTTP 客户端
│   │   ├── contexts/      # React Context
│   │   │   ├── ThemeProvider.tsx
│   │   │   ├── ToastProvider.tsx
│   │   │   └── WebSocketProvider.tsx
│   │   ├── hooks/         # 自定义 Hooks
│   │   └── store/         # Zustand 状态管理
│   ├── dist/              # 前端构建输出
│   ├── rsbuild.config.ts  # Rsbuild 配置
│   ├── biome.json         # Biome 代码规范配置
│   ├── tsconfig.json      # TypeScript 配置
│   ├── package.json       # 前端依赖
│   └── pnpm-lock.yaml     # pnpm 锁文件
├── resources/             # 静态资源
│   ├── Img/               # 图标、图片资源
│   ├── fonts/             # 字体文件
│   ├── mapping_table/     # 演员/信息映射表
│   ├── c_number/          # 中文番号映射
│   └── zhconv/            # 简繁转换字典
├── libs/                  # 额外 DLL（Windows 用）
├── .github/workflows/     # CI/CD 配置
│   ├── ci.yaml            # 持续集成
│   ├── release.yml        # 正式发布（Python 3.13 + PyInstaller）
│   └── release.v1.yml     # 旧版发布
└── .pre-commit-config.yaml # Pre-commit 钩子配置
```

---

## 模块功能说明

### `mdcx/config/` - 配置管理

基于 Pydantic (pydantic-settings) 的配置管理系统。核心组件：

- **`models.py`** - `Config` 类是 Pydantic BaseModel，定义所有可配置项的字段名、类型和默认值。新增配置项在此文件中添加字段。
- **`manager.py`** - `ConfigManager` 单例，负责从 JSON 文件加载配置、保存配置、处理 V1 旧版配置迁移。通过 `from mdcx.config.manager import manager` 导入，使用 `manager.config.<key>` 访问配置项。
- **`enums.py`** - 配置相关枚举（网站、语言、开关等）。
- **`computed.py`** - 基于原始配置计算出的派生属性（如文件路径拼接等）。
- **`resources.py`** - 静态资源（图标、字体等）的路径管理。
- **`ui_schema.py`** - 生成 JSON Schema 和 UI Schema，供 WebUI 前端动态渲染设置表单。
- **`v1.py`** - 旧版 `.ini` 格式配置文件的读取和迁移逻辑。

### `mdcx/core/scraper.py` - 核心刮削工作流

主刮削流程编排器，负责协调整个刮削流程：

1. **扫描文件** → 读取目录，识别视频、图片文件
2. **提取番号** → 从文件名中解析番号
3. **并发爬取** → 调用各网站爬虫获取元数据
4. **翻译** → 翻译标题、简介、演员名
5. **下载资源** → 封面、缩略图、预告片、剧照
6. **生成 NFO** → 构建 Kodi/Emby 兼容的元数据文件
7. **整理文件** → 移动/重命名/符号链接

### `mdcx/crawlers/` - 网站爬虫

每个网站一个 `.py` 文件，继承 `mdcx.crawlers.base.base.GenericBaseCrawler`。爬虫基类定义了标准的爬取生命周期：

- `base_url_()` - 返回网站默认 URL
- `_fetch_detail()` - 请求详情页 HTML
- `_parse()` - 解析 HTML，提取元数据
- `run()` - 完整爬取流程入口

通过 `mdcx/crawlers/__init__.py` 中的注册表将 `Website` 枚举映射到对应的爬虫类。

`base/parser.py` 提供了基于 CSS 选择器的声明式解析器框架。

### `mdcx/server/` - FastAPI Web 服务

基于 FastAPI 的 Web 后端，提供：

- **REST API** (`api/v1/`) - 配置读写、文件浏览、刮削触发、传统兼容接口
- **WebSocket** (`ws/`) - 实时日志推送、状态更新
- **认证** - API Key 鉴权 + WebSocket 协议升级认证
- 静态文件服务 - 托管前端构建产物 (`ui/dist`)

### `mdcx/controllers/` - Qt 事件处理

Qt 桌面版的控制器层，桥接 UI 和业务逻辑：

- **`main_window/init.py`** - `Init_Ui()` 初始化窗口属性、图标、菜单，`Init_Singal()` 绑定信号/槽
- **`main_window/main_window.py`** - `MyMAinWindow` 主窗口类，包含刮削启动、停止等核心事件处理
- **`main_window/handlers.py`** - 各类 UI 事件的处理函数
- **`main_window/load_config.py`** - 将 `Config` 对象的值加载到对应 UI 控件
- **`main_window/save_config.py`** - 从 UI 控件读取值并更新 `Config` 对象
- **`main_window/bind_utils.py`** - 控件双向绑定工具函数

### `mdcx/views/` - Qt UI 定义

Qt Designer 生成的 `.ui` XML 文件和编译后的 `.py` Python 代码。修改 UI 布局后需要重新编译。

### `mdcx/tools/` - 独立工具

独立于主刮削工作流的工具模块：
- `emby_actor_image.py` - 更新 Emby 演员头像
- `emby_actor_info.py` - 生成 Kodi/Emby 演员 NFO
- `missing.py` - 检测缺失元数据的影片
- `subtitle.py` - 字幕文件处理
- `wiki.py` - 维基百科信息查询

### `ui/` - React 前端

基于 **Rsbuild** 构建的 React 单页应用，技术栈：

| 技术 | 用途 |
|------|------|
| React 19 | UI 框架 |
| MUI 7 | 组件库 |
| TanStack Router | 路由管理 |
| TanStack Query | 服务端状态管理 |
| RJSF | JSON Schema 动态表单 |
| Zustand | 客户端状态管理 |
| @hey-api/openapi-ts | OpenAPI 客户端生成 |
| Biome | 代码检查与格式化 |

前端通过 OpenAPI 规范自动生成 HTTP 客户端 (`src/client/`)，与后端 API 保持类型同步。

---

## 运行方式

### Qt 桌面版

```powershell
uv run python main.py
```

### Web 服务版

```powershell
# 先构建前端
cd ui
pnpm build
cd ..

# 启动 FastAPI 开发服务器
$env:MDCX_DEV=1
fastapi dev server.py
```

启动后访问 `http://localhost:8000` 即可使用 WebUI。
设置环境变量 `MDCX_DEV=1` 可启用开发模式（关闭认证等）。

### 前端开发服务器（热更新）

```powershell
cd ui
pnpm dev
```

前端开发服务器运行在 `http://localhost:3010`，需要同时启动后端服务。

---

## 打包构建 (Windows)

### 构建 PyInstaller 可执行文件

```powershell
# 构建 Windows 版
uv run scripts/build.py --debug

# 指定应用名称和版本
uv run scripts/build.py --app-name MDCx --version 20250101

# macOS 额外选项
uv run scripts/build.py --create-dmg --version 20250101 --debug
```

构建输出在 `dist/` 目录。

### 前端构建

```powershell
cd ui
pnpm build
# 输出到 ui/dist/
```

### CI 构建

正式发布使用 GitHub Actions，配置见 `.github/workflows/release.yml`：
- 触发条件：发布 Release 或推送版本标签
- 使用 `astral-sh/setup-uv@v6` 安装 uv，从 `pyproject.toml` 读取 Python 版本
- `uv sync --locked --all-extras --dev` 安装依赖
- `uv run scripts/build.py --debug` 执行构建
- 产物通过 `svenstaro/upload-release-action` 上传到 Release

---

## 测试

### 运行所有测试

```powershell
uv run pytest
```

### 运行单个测试文件

```powershell
uv run pytest tests/test_config_conversion.py
uv run pytest tests/crawlers/
```

### 爬虫调试工具

`crawl` CLI 命令用于独立调试爬虫：

```powershell
# 查看帮助
uv run crawl --help

# 通过番号爬取指定网站
uv run crawl --site javbus --number SSNI-111

# 通过 URL 爬取
uv run crawl --site javbus --appoint-url https://www.javbus.com/SSNI-111

# 保存结果到文件
uv run crawl --site javbus --number SSNI-111 --output result.json

# 使用代理
uv run crawl --site javbus --number SSNI-111 --proxy http://127.0.0.1:7890
```

---

## UI 修改流程

1. 使用 **Qt Designer** 或 **Qt Creator** 打开并编辑 `mdcx/views/MDCx.ui`（主窗口）或 `mdcx/views/posterCutTool.ui`（裁剪窗口）。

2. 运行编译脚本生成 Python 代码：

   ```powershell
   bash ./scripts/pyuic.sh
   # 或直接运行：
   pyuic5 mdcx/views/MDCx.ui -o mdcx/views/MDCx.py
   ```

3. 在 `mdcx/controllers/main_window/init.py` 的 `Init_Singal()` 函数中绑定新增控件的信号/槽。

4. 事件处理函数添加：
   - 控件事件处理 → `mdcx/controllers/main_window/main_window.py`
   - 配置/业务事件处理 → `mdcx/controllers/main_window/handlers.py`

5. 如果是配置相关的控件：
   - 在 `mdcx/controllers/main_window/load_config.py` 中添加配置 → UI 的加载逻辑
   - 在 `mdcx/controllers/main_window/save_config.py` 中添加 UI → 配置的保存逻辑

---

## 代码规范

### Python (Ruff)

配置见 `ruff.toml`：
- **行宽**: 120
- **缩进**: 4 空格
- **引号**: 双引号
- **启用的规则**: isort (I), pyupgrade (UP), pycodestyle (E), Pyflakes (F), flake8-bugbear (B), flake8-comprehensions (C4), FAST 等
- **格式化**: `ruff format`（类似 Black）

```powershell
# 检查
uv run ruff check

# 自动修复
uv run ruff check --fix

# 格式化
uv run ruff format
```

### 前端 (Biome)

配置见 `ui/biome.json`：
- **行宽**: 120
- **缩进**: 2 空格
- **引号**: 双引号
- **启用规则**: recommended + 未使用导入检查

```powershell
cd ui

# 检查
pnpm lint

# CI 检查（只读）
pnpm ci
```

### Pre-commit

提交前自动执行 `ruff check --fix` 和 `ruff format`（在 `pre-merge-commit` 和 `pre-push` 阶段触发）：

```powershell
# 手动运行所有钩子
uv run pre-commit run --all-files
```
