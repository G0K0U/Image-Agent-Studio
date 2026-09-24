# 🌸 Image Agent Studio (中文版说明)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![ComfyUI Compatible](https://img.shields.io/badge/ComfyUI-API%20Engine-brightgreen.svg)](https://github.com/comfyanonymous/ComfyUI)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](./LICENSE)

> [English Documentation](./README.md) | **中文文档**

**Image Agent Studio** 是一个专为消费级显卡（如 RTX 4080 16GB）设计的下一代 AI 生图智能体工作台。

它通过**智能显存接力（Strict VRAM Handover）**机制，将**本地多模态大语言模型（如 Heretic Qwen 3.8 27B）**与 **ComfyUI 顶尖生图引擎**无缝融合，原生支持两大旗舰级工作流：
1. **✨ Qwen-Image 2.1 进阶引擎 (SevnFading Advanced)**：支持全中文自然语言对话出图、多模态看图改图、局部属性解耦精准编辑（文生图 / 图生图）。
2. **🌸 Anima AIO Yuri (SDXL 动漫专精)**：专业级 Danbooru 动漫微调基底，支持多 LoRA 动态调度与去噪控制。

---

## ⚡ 核心优势

- **严格显存接力（0 冲突，0 爆显存）**：
  在 16GB 显存环境下，Agent 大模型（27B）按需调入显存进行短上下文（-c 4096）快速规划（约 5 秒），规划完毕后**立即释放卸载**，将 100% 显存完全让渡给 ComfyUI 满血渲染。
- **双模态智能提示词重写引擎**：
  - **Qwen 模式**：内置阿里官方 Qwen-Image 2.1 电影级长篇提示词扩写协议与多图属性解耦协议。
  - **Anima 模式**：内置高质量 Danbooru 标签自动扩展与多 LoRA 权重智能调度。
- **干净模板化设计**：
  仓库内仅包含纯净 API 工作流模板，不携带任何个人本地提示词、测试历史或个人图片。
- **Agent 一键自动部署**：
  专门为 AI Coding Agent（如 Claude Code, Google Antigravity, Codex, Cursor）提供完整的自动化执行协议。

---

## 🤖 交给 AI Agent 一键部署 (推荐)

如果你正在使用 AI 编程助手（Claude Code, Antigravity, Codex, Cursor 等），直接向它发送以下提示词即可：

> **“请读取本项目中的 [AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md)，帮我在本地自动检查并安装所需的 ComfyUI 节点，校验模型与 LoRA，配置好 config.json 并启动 Image Agent Studio。”**

Agent 会自动根据清单完成环境探测、节点克隆以及模型校验。

---

## 🛠️ 人工部署步骤

### 1. 克隆本仓库并安装依赖
```bash
git clone https://github.com/G0K0U/Image-Agent-Studio.git
cd Image-Agent-Studio
pip install -r requirements.txt
```

### 2. 自动安装 ComfyUI 所需扩展节点
运行环境自检脚本，指定你的 ComfyUI 根目录：
```bash
python scripts/setup_environment.py --comfy-dir /path/to/ComfyUI
```
脚本将自动为你克隆所需的 11 个核心自定义节点（如 `ComfyUI-GGUF`、`rgthree-comfy` 等）。

### 3. 检查与下载模型权重
运行模型清单自检工具：
```bash
python scripts/download_models.py --models-dir /path/to/ComfyUI/models
```
该工具会检查缺失的模型，并生成 `huggingface-cli` 一键下载命令。

#### 核心模型推荐清单：
- **Qwen-Image 2.1**:
  - Diffusion: `qwen-image-2.1-Q4_K_M.gguf` (`city96/Qwen-Image-2.1-GGUF`)
  - Text Encoder: `qwen3vl_8b_int8_convrot.safetensors` (`Comfy-Org/Qwen-Image-2.1-GGUF`)
  - VAE: `qwen_image_2.1_vae_bf16.safetensors` (`Comfy-Org/Qwen-Image-2.1-GGUF`)
- **Anima Yuri**:
  - Checkpoint: `miaomiaoHarem_animaBase.safetensors` 或 `Anima-2.9B-preview-v1.safetensors`
  - Core LoRAs: `RealSkin`, `aesthetic`, `detailer`, `Scenery_enchancer`, `darklight`, `colorfix`
- **本地 Agent LLM**:
  - `Qwen3.8-27B-Heretic-Ara-iq4_xs-3.0-mtp.gguf`（或任何兼容 OpenAI 接口的本地模型服务）

### 4. 配置 `config.json`
复制 `config.example.json` 为 `config.json`，根据本地环境配置端口与路径：
```json
{
  "comfy_api_url": "http://127.0.0.1:8191",
  "comfy_input_dir": "./ComfyUI/input",
  "comfy_output_dir": "./ComfyUI/output",
  "studio_port": 7860,
  "heretic_api_url": "http://127.0.0.1:18200/v1/chat/completions",
  "heretic_model_name": "Qwen3.8-27B-Heretic-Ara-iq4_xs-3.0-mtp.gguf"
}
```

### 5. 启动控制台
```bash
python web_gui.py
```
访问浏览器控制台：**[http://127.0.0.1:7860](http://127.0.0.1:7860)**。

---

## 🎨 工作流模板说明

所有模板均放置于 `workflows/` 目录中：
- **`qwen-image-2.1-t2i-template.json`**：纯净文生图 API 拓扑图，由 Heretic 27B 直接注入摄影级提示词与长宽比。
- **`qwen-image-2.1-i2i-template.json`**：图生图 / 图像属性解耦编辑 API 拓扑图，支持结合参考底图定向修改细节。
- **`anima-yuri-aio-template.json`**：Anima SDXL 动漫 API 拓扑图，包含多级 LoRA 堆叠与去噪控制。
- **`reference-sevnfading-advanced.json`**：原始 SevnFading 进阶工作流完整界面图，可直接拖入 ComfyUI 画布查看与编辑。

---

## 📜 许可证

MIT License.
