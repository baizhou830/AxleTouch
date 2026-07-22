# AxleTouch


![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg) 
![Python](https://img.shields.io/badge/Python-3.12%2B-blue) 

雨竹Bot-一个轻量化桌宠，基于 PyQt5 实现。  
桌面宠物会贴边吸附，单击弹出输入框，支持与 AI 对话并展示气泡回复。

## 功能

- **贴边吸附** — 拖拽后自动吸附到屏幕左/右侧
- **AI 对话** — 单击桌宠弹出输入框，AI 回复以气泡形式展示
- **定时问候** — 定时获取当前窗口状态并主动发起对话
- **多模型支持** — 支持以下 AI 厂商：
  - **阶跃星辰** (`step-3.7-flash`)
  - **阿里百炼** (`qwen-turbo`)
  - **DeepSeek** (`deepseek-chat`)
- **多模态支持** — 暂时只支持StepFun 拖拽图片到输入框可发送图片进行识别
（预告：下个版本将会加入更多的多模态支持。）
- **右键菜单** — 右键桌宠可打开 GUI 设置、退出程序或邀请雨竹查看屏幕
- **查看屏幕** — 右键可邀请雨竹查看屏幕
- **web搜索** — 在配置了tavilyAPI后 雨竹可进行web搜索

## 安装与运行

### 快速开始

 **EXE打包版本**: 
 [Releases 页面](https://github.com/baizhou830/AxleTouch/releases)
直接下载 `AxleTouch.zip`，解压后双击其中的exe即可。

 **release分发太慢，需要本地打包？**
 [请点此处](https://github.com/baizhou830/AxleTouch/releases/tag/v1.0)
 下载此release中的build.py以本地打包。

---

### 二次开发/调试
```cmd
# 1. 同步依赖（如遇 SSL 证书错误，加 --system-certs）
uv sync --system-certs

# 2. 运行
uv run axle-touch

# 首次启动会自动生成 config.json
# 右键桌宠 → 配置文件设置，选择厂商并填入 API Key
```

## 配置文件

首次启动自动在 exe 同目录下生成 `config.json`，也可通过 GUI 设置界面修改：

```json
{
    "provider": "stepfun",
    "api_key": "",
    "tavily_api_key": "",   
    "icon_size": 100,
    "popup_width": 420,
    "prompt": DEFAULT_PROMPT,
}
```

| 厂商 | provider 值 | 获取 API Key |
|------|-------------|-------------|
| 阶跃星辰 | `stepfun` | [platform.stepfun.com](https://platform.stepfun.com) |
| 阿里百炼 | `bailian` | [bailian.console.aliyun.com](https://bailian.console.aliyun.com) |
| DeepSeek | `deepseek` | [platform.deepseek.com](https://platform.deepseek.com) |



## 依赖

- Python 3.8+
- PyQt5

## 数据收集与隐私声明

详见 [PRIVACY](PRIVACY.md) 文件。

## 许可证

本项目基于 **GNU General Public License v3** 开源。  
详见 [LICENSE](LICENSE) 文件。
