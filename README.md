# MDCx

日本电影元数据抓取工具，配合 Emby、Kodi、Plex 等本地影片管理软件使用，自动从在线网站抓取影片元数据并生成 NFO 文件。

## 功能特点

- 支持 40+ 网站爬虫（javbus、javdb、dmm、fc2、mgstage 等）
- Qt 桌面客户端与 Web 服务（React 前端）两种运行方式
- 正常、视频、更新、读取四种刮削模式
- 软链接 / 硬链接模式支持
- AI 翻译（LLM）、多代理支持
- 自动命名、分类与移动
- Kodi / Emby / Plex 兼容的 NFO 文件生成

## 下载

至 [Releases](https://github.com/sqzw-x/mdcx/releases) 页面下载最新版本。

## 构建

```bash
uv sync --all-extras --dev
uv run build --app-name MDCx
```

要求 Python >= 3.13.4，使用 [uv](https://docs.astral.sh/uv/) 管理依赖，[pnpm](https://pnpm.io/) 管理前端。

## 许可证

MIT
