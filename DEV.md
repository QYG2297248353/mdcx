# MDCx 开发文档

## 环境准备

### 1. 安装 Python 环境

推荐使用 Miniconda 管理 Python 版本：

```powershell
conda create -n mdcx python=3.13
conda activate mdcx
```

### 2. 安装 uv（Python 包管理）

```powershell
pip install uv
```

### 3. 安装 Node.js 和 pnpm（仅 WebUI 开发需要）

```powershell
# 安装 Node.js: https://nodejs.org/
npm install -g pnpm
```

### 4. 克隆仓库并安装依赖

```powershell
git clone https://github.com/sqzw-x/mdcx.git
cd mdcx

# 安装 Python 依赖（含 PyQt5、开发工具等）
conda activate mdcx
uv sync --all-extras --dev

# 仅开发 WebUI 才需要安装前端依赖
cd ui
pnpm install
cd ..
```

`uv sync` 完成后，`.venv\Scripts\` 下可用关键工具：

| 工具 | 用途 |
|------|------|
| `python.exe` | Python 解释器 |
| `pyuic5.exe` | Qt .ui → .py 编译器 |
| `fastapi.exe` | Web 服务端 |
| `ruff.exe` | 代码检查/格式化 |

---

## 快速启动

### 启动 Qt 桌面版（主要开发模式）

```powershell
# 确保在 conda 环境中
conda activate mdcx

# 直接启动
python main.py
```

### 启动 Web 服务版（次要，仅 WebUI 开发使用）

```powershell
# 终端 1：启动后端
$env:MDCX_DEV = "1"
.\.venv\Scripts\fastapi.exe dev server.py --host 127.0.0.1 --port 8000

# 终端 2：启动前端热更新
cd ui
pnpm dev
# 访问 http://localhost:3010
```

---
## 配置持久化机制 🔴 必读

**修改 `models.py` 中的默认值后，Qt 界面可能不生效——这不是 bug，是设计如此。**

程序启动时的加载优先级：

```
1. 读取 config.json（磁盘上持久化的值）      ← 优先
2. 对 config.json 中不存在的字段，用 models.py 中的 Field(default=...) 补默认值  ← 兜底
```

**如果 `config.json` 已存在且包含该字段，models.py 的默认值完全被忽略。**

### 解决方案

```powershell
# 关闭 Qt 程序后，删除配置让程序用新默认值重建
del config.json
python main.py
```

> `config.json` 位于项目根目录（`MAIN_PATH / "config.json"`），由 `ConfigManager` 管理。每次在 Qt 界面中点击"保存"，config.json 就会被覆盖写入。

---
## Qt 桌面版开发流程 🔴 核心

MDCx 是 Qt 桌面应用，**绝大部分功能开发都走 Qt 路径**。WebUI 是辅助入口。

### 架构分层

修改一个功能涉及 **4 层代码**，缺一层 Qt 界面就不会显示变化：

```
Layer 1: 数据定义
  mdcx/config/enums.py      → 枚举值定义
  mdcx/config/models.py     → 配置字段定义

Layer 2: UI 控件（必须双文件同步）
  mdcx/views/MDCx.ui        → Qt Designer XML（控件定义）
  mdcx/views/MDCx.py        → Python 编译产物（与 .ui 一一对应）

Layer 3: 控件绑定
  mdcx/controllers/main_window/load_config.py  → 启动时：配置 → UI
  mdcx/controllers/main_window/save_config.py  → 保存时：UI → 配置

Layer 4: 业务逻辑
  mdcx/base/                → 底层功能实现
  mdcx/core/                → 编排调度
```

### 完整的 UI 控件生命周期

以新增一个 CheckBox 控件为例，说明文件间的依赖关系：

```
MDCx.ui (XML)
  <widget class="QCheckBox" name="checkBox_my_new_feature">
    ↓ pyuic5 编译
MDCx.py (Python)
  self.checkBox_my_new_feature = QCheckBox(...)
    ↓ 运行时创建控件
load_config.py
  set_checkboxes(..., (self.Ui.checkBox_my_new_feature, ...))
    ↓ 启动时从配置加载到 UI
[用户操作控件 in Qt 界面]
    ↓ 用户点击保存
save_config.py
  get_checkboxes(..., (self.Ui.checkBox_my_new_feature, ...))
    ↓ 回写到配置
models.py (Pydantic Config)
  持久化到 JSON 配置文件
```

### 方案A：有 Qt Designer（推荐，但非必须）

```powershell
# 1. 安装 Qt Designer（Windows）
pip install pyqt5-tools
# Designer 在 .venv\Scripts\pyqt5-tools\designer.exe
# 或自行下载：https://build-system.fman.io/qt-designer-download

# 2. 用 Qt Designer 打开并编辑 .ui 文件
designer.exe mdcx/views/MDCx.ui

# 3. 保存 .ui 后，编译为 .py
.\.venv\Scripts\pyuic5.exe mdcx/views/MDCx.ui -o mdcx/views/MDCx.py

# 4. 编辑控制器绑定新控件（见"Layer 3: 控件绑定"）

# 5. 重启 python main.py
```

### 方案B：无 Qt Designer，手动编辑（常见情况）

**直接同步编辑 .ui 和 .py 两个文件。** 两者格式不同但一一对应：

| .ui (XML) | .py (Python) |
|-----------|-------------|
| `<widget class="QCheckBox" name="checkBox_xxx">` | `self.checkBox_xxx = QtWidgets.QCheckBox(...)` |
| `<property name="text"><string>显示名</string></property>` | `self.checkBox_xxx.setText(_translate("MDCx", "显示名"))` |
| `<property name="minimumSize"><size><width>93</width><height>30</height></size></property>` | `self.checkBox_xxx.setMinimumSize(QtCore.QSize(93, 30))` |

**操作步骤：**
1. 在 `.ui` 中找到目标布局（如 `horizontalLayout_20`），添加新控件的 XML 块
2. 在 `.py` 中找到同一个 layout 的 `addWidget` 位置，添加对应的 Python 代码
3. 在 `.py` 末尾的 `retranslateUi` 方法中添加 `setText` 行
4. 编辑 `load_config.py` 和 `save_config.py`（见下方）

### Layer 3: 控件绑定（无论方案A或B都必须做）

**load_config.py** — 启动时将配置值加载到 UI 控件：

```python
# CheckBox 类型（如翻译引擎选择）
set_checkboxes(
    manager.config.translate_config.translate_by,
    (self.Ui.checkBox_youdao, Translator.YOUDAO),
    (self.Ui.checkBox_google, Translator.GOOGLE),
    (self.Ui.checkBox_ammds, Translator.AMMDS),   # 新增
)

# TextEdit 类型
self.Ui.lineEdit_llm_key.setText(manager.config.translate_config.llm_key)

# ComboBox 类型
self.Ui.comboBox_website_all.setCurrentIndex(index)
```

**save_config.py** — 保存时将 UI 控件值回写到配置：

```python
# CheckBox 类型
manager.config.translate_config.translate_by = get_checkboxes(
    (self.Ui.checkBox_youdao, Translator.YOUDAO),
    (self.Ui.checkBox_google, Translator.GOOGLE),
    (self.Ui.checkBox_ammds, Translator.AMMDS),   # 新增
)

# QLineEdit 类型
manager.config.translate_config.llm_key = self.Ui.lineEdit_llm_key.text()

# ComboBox 类型
manager.config.website_single = Website(self.Ui.comboBox_website_all.currentText())
```

**ComboBox（下拉框）特殊处理**：Qt 的 ComboBox 是索引绑定，不是在 load/save 中映射。需要在 `.ui` 和 `.py` 中直接添加 item：

| .ui (XML) | .py (Python) |
|-----------|-------------|
| `<item><property name="text"><string>ammds</string></property></item>` | `self.comboBox_website_all.addItem("")`<br>`self.comboBox_website_all.setItemText(35, _translate("MDCx", "ammds"))` |

---

## 典型案例：新增翻译引擎

以下是在 Qt 中新增一个翻译引擎（如 AMMDS）的**完整文件清单**：

| 步骤 | 文件 | 操作 |
|------|------|------|
| 1 | `mdcx/config/enums.py` | 在 `Translator` 枚举中添加 `AMMDS = "ammds"` |
| 2 | `mdcx/config/models.py` | 在 `translate_by` 默认值列表末尾追加 `Translator.AMMDS` |
| 3 | `mdcx/views/MDCx.ui` | 在 `horizontalLayout_20` 中添加 `checkBox_ammds` 的 XML |
| 4 | `mdcx/views/MDCx.py` | 添加 `checkBox_ammds` 的创建代码 + `setText` 行 |
| 5 | `mdcx/controllers/main_window/load_config.py` | `set_checkboxes()` 中追加 `(checkBox_ammds, AMMDS)` |
| 6 | `mdcx/controllers/main_window/save_config.py` | `get_checkboxes()` 中追加 `(checkBox_ammds, AMMDS)` |
| 7 | `mdcx/base/translate.py` | 实现 `ammds_translate()` 函数 |
| 8 | `mdcx/core/translate.py` | `_task()` 中新增 `Translator.AMMDS` 分支 |

**如果还涉及 ComboBox（下拉框）选择网站，则额外需要：**

| 步骤 | 文件 | 操作 |
|------|------|------|
| 9 | `mdcx/views/MDCx.ui` | 在 `comboBox_website_all` 的 item 列表末尾追加 `<item>` |
| 10 | `mdcx/views/MDCx.py` | 追加 `addItem("")` + `setItemText(N, "ammds")` |

> **注意**：`.ui` 和 `.py` 中的控件数量必须一致（如 addItem 35 个 → setItemText 0~34），否则索引偏移会导致 ComboBox 内容错乱。

---

## 典型案例：新增刮削网站

| 步骤 | 文件 | 操作 |
|------|------|------|
| 1 | `mdcx/config/enums.py` | `Website` 枚举添加 `NEWSITE = "newsite"` |
| 2 | `mdcx/config/models.py` | 各字段 `site_prority` 默认列表添加 `Website.NEWSITE` |
| 3 | `mdcx/crawlers/newsite.py` | 实现爬虫 `GenericBaseCrawler` 子类 |
| 4 | `mdcx/crawlers/__init__.py` | 注册爬虫映射 |
| 5 | `mdcx/views/MDCx.ui` | `comboBox_website_all` 追加 item |
| 6 | `mdcx/views/MDCx.py` | 追加 `addItem` + `setItemText` |

> LineEdit（文本输入框）类型的网站配置（如 `lineEdit_website_youma`）**不需要手动修改控制器**。`load_config.py` 和 `save_config.py` 通过 `",".join(...)` 和 `get_sites()` 函数自动处理，用户在文本框中输入 `newsite` 即可。

---

## 目录结构

（见下方项目树）

```
mdcx/
├── main.py                # Qt 桌面版入口 ⭐ 主要入口
├── server.py              # FastAPI Web 服务入口（次要）
├── pyproject.toml         # Python 项目配置
├── uv.lock                # 依赖锁文件
├── mdcx/
│   ├── config/
│   │   ├── enums.py       # 枚举定义：Translator, Website, Language 等
│   │   ├── models.py      # Pydantic 配置模型：Config, TranslateConfig 等
│   │   ├── manager.py     # ConfigManager 单例，JSON 配置加载/保存
│   │   └── ...
│   ├── views/             # Qt UI 定义（双文件同步）
│   │   ├── MDCx.ui        # Qt Designer XML ⭐ 控件定义源文件
│   │   └── MDCx.py        # pyuic5 编译产物 ⭐ 必须与 .ui 同步
│   ├── controllers/       # Qt 控制器
│   │   └── main_window/
│   │       ├── load_config.py  # 启动时：配置 → UI 控件 ⭐
│   │       ├── save_config.py  # 保存时：UI 控件 → 配置 ⭐
│   │       ├── bind_utils.py   # set_checkboxes / get_checkboxes 工具
│   │       ├── main_window.py  # 主窗口类
│   │       └── init.py         # UI 初始化、信号绑定
│   ├── base/              # 基础功能
│   │   └── translate.py   # 翻译底层实现（各引擎 API 调用）
│   ├── core/              # 核心工作流
│   │   ├── scraper.py     # 主刮削流程
│   │   └── translate.py   # 翻译编排（按优先级逐引擎 fallback）
│   ├── crawlers/          # 网站爬虫（~40个）
│   │   ├── __init__.py    # 爬虫注册表
│   │   └── *.py           # 各网站实现
│   └── server/            # Web 后端
├── ui/                    # WebUI 前端（RSbuild + React + MUI）
│   └── src/client/        # 自动生成的 OpenAPI 客户端（不要手动编辑）
├── resources/             # 静态资源
├── scripts/               # 构建脚本
└── tests/                 # 测试
```

---

## WebUI 开发流程（次要）

WebUI 通过 JSON Schema 自动驱动配置表单。Python 修改后需要重新生成前端类型。

```
Python Pydantic (enums.py, models.py)
    ↓ FastAPI
OpenAPI Schema (http://localhost:8000/openapi.json)
    ↓ pnpm gen:client
TypeScript 类型 (ui/src/client/)
    ↓ pnpm build / pnpm dev
WebUI 更新
```

```powershell
# 1. 启动后端
$env:MDCX_DEV = "1"
.\.venv\Scripts\fastapi.exe dev server.py --host 127.0.0.1 --port 8000

# 2. 重新生成前端类型
cd ui
pnpm gen:client

# 3. 启动前端开发服务器或构建
pnpm dev    # 开发模式，热更新
# 或
pnpm build  # 生产构建
```

---

## 测试

```powershell
uv run pytest                          # 全部测试
uv run pytest tests/crawlers/          # 爬虫测试
uv run crawl --site javbus --number SSNI-111   # 爬虫调试
```

---

## 打包构建

```powershell
uv run scripts/build.py --debug
# 输出：dist/MDCx.exe (Windows) 或 dist/MDCx.app (macOS)
```

---

## 代码规范

```powershell
uv run ruff check              # Python lint
uv run ruff check --fix        # Python 自动修复
uv run ruff format             # Python 格式化

cd ui && pnpm lint             # 前端 lint
```
