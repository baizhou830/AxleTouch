# AxleTouch


![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg) 
![Python](https://img.shields.io/badge/Python-3.8%2B-blue) 


一个轻量化桌宠，基于 PyQt5 实现。  
桌面宠物会贴边吸附，单击弹出输入框，支持与 AI 对话并展示气泡回复。

## 功能

- **贴边吸附** — 拖拽后自动吸附到屏幕左/右侧
- **AI 对话** — 单击桌宠弹出输入框，AI 回复以气泡形式展示
- **定时问候** — 定时获取当前窗口状态并主动发起对话
- **图片识别** — 拖拽图片到输入框可发送图片进行识别
- **多模型支持** — 支持以下 AI 厂商，也可自定义任意兼容 OpenAI API 的厂商（设置中需填写模型名称）：
  - **阶跃星辰**
  - **阿里百炼**
  - **DeepSeek**
  - **硅基流动**
- **自定义 Prompt** — 右键菜单可编辑 AI 角色设定（System Prompt）
- **右键菜单** — 右键桌宠可打开 GUI 设置或退出程序

## 快速开始

```bash
# 1. 同步依赖（如遇 SSL 证书错误，加 --system-certs）
uv sync

# 2. 运行
uv run python main.py

# 首次启动会自动生成 config.toml
# 右键桌宠 → 配置文件设置，选择厂商、填写 API Key 和模型名称
```

## 配置文件

首次启动自动在 exe 同目录下生成 `config.toml`，也可通过 GUI 设置界面修改：

```toml
provider = "stepfun"
model = ""
api_key = ""
```

| 厂商 | provider 值 | 获取 API Key |
|------|-------------|-------------|
| 阶跃星辰 | `stepfun` | [platform.stepfun.com](https://platform.stepfun.com) |
| 阿里百炼 | `bailian` | [bailian.console.aliyun.com](https://bailian.console.aliyun.com) |
| DeepSeek | `deepseek` | [platform.deepseek.com](https://platform.deepseek.com) |
| 硅基流动 | `siliconflow` | [siliconflow.cn](https://siliconflow.cn) |
| 自定义 | `custom` | 自行填写接口地址和模型名称 |

## 打包为单文件 exe

可使用 PyInstaller 打包为单文件 exe，无需 Python 环境即可运行。

```bash
# 使用 uv 打包（推荐）
uv run --system-certs build.py

# 或直接使用 Python
python build.py
```

打包后的 `AxleTouch.exe` 位于 `dist/` 目录下（约 38 MB），exe 自带图标。

> `assets/` 目录已内嵌到 exe 中，`config.toml` 首次运行会自动在 exe 同目录下生成。

## 依赖

- Python 3.8+
- PyQt5

## 许可证

本项目基于 **GNU General Public License v3** 开源。  
详见 [LICENSE](LICENSE) 文件。
