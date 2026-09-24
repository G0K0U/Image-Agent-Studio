# 🌸 Image Agent Studio

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![ComfyUI Compatible](https://img.shields.io/badge/ComfyUI-API%20Engine-brightgreen.svg)](https://github.com/comfyanonymous/ComfyUI)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](./LICENSE)
[![Bilingual](https://img.shields.io/badge/Language-English%20%7C%20%E4%B8%AD%E6%96%87-orange.svg)](#-中文文档-chinese-documentation)

> [English](#-english-documentation) | [中文文档](#-中文文档-chinese-documentation)

---

# 📖 English Documentation

**Image Agent Studio** is a next-generation AI image generation workspace tailored for consumer GPUs (e.g., RTX 4080 16GB VRAM).

It bridges a **local Vision-Language LLM Agent (e.g., Heretic Qwen 3.8 27B / llama.cpp / Ollama)** with the **ComfyUI generation backend** through an automated **Strict VRAM Handover** mechanism, providing native support for two flagship workflows:

1. **✨ Qwen-Image 2.1 Advanced Engine (SevnFading Advanced)**: Text-to-Image (T2I), Image-to-Image (I2I), and Multimodal Attribute-Disentangled Local Editing using official Alibaba prompt rewriting standards.
2. **🌸 Anima AIO Yuri Engine (SDXL Anime Specialization)**: High-fidelity Danbooru anime generation with dynamic multi-LoRA stacking and denoise control.

---

## ⚡ Key Highlights

- **Strict VRAM Handover (Zero GPU Memory Contention)**:
  On 16GB GPUs, running a 27B LLM alongside diffusion models causes Out-Of-Memory (OOM) errors. Image Agent Studio boots the LLM on-demand with short context (`-c 4096`), completes reasoning and workflow parameter planning in ~5 seconds, and **immediately unloads the LLM**, granting 100% of GPU VRAM exclusively to ComfyUI for generation.
- **Dual-Engine Prompt Optimization**:
  - **Qwen Mode**: Expands simple natural language into cinematic photographic descriptions (camera lens, depth-of-field, lighting, textures) and performs visual attribute disentanglement for precision editing.
  - **Anima Mode**: Expands prompts into Danbooru-style tag syntax with negative suppression and automatic LoRA weighting.
- **Pure Template Architecture**:
  The repository contains only sanitized, reproducible API templates without personal prompts, test history, or local image artifacts.
- **1-Click AI Agent Deployment**:
  Designed specifically so that autonomous coding agents (Claude Code, Google Antigravity, OpenAI Codex, Cursor) can deploy the complete stack autonomously with a single user prompt.

---

## 🤖 1-Click Deployment via AI Agent (Recommended)

If you are using an AI Coding Assistant (**Claude Code, Antigravity, Codex, Cursor, RooCode**), simply paste this instruction to your agent:

> **"Please read [AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md) and deploy Image Agent Studio. Automatically check and install required ComfyUI custom nodes, inspect and guide downloading required weights and LoRAs, initialize `config.json`, and launch the web studio."**

The agent will execute the verified deployment protocol autonomously.

---

## 🛠️ Manual Installation Guide

### 1. Clone Repository & Install Python Dependencies
```bash
git clone https://github.com/G0K0U/Image-Agent-Studio.git
cd Image-Agent-Studio
pip install -r requirements.txt
```

### 2. Auto-Install Required ComfyUI Custom Nodes
Run the automated environment setup script pointing to your ComfyUI directory:
```bash
python scripts/setup_environment.py --comfy-dir /path/to/ComfyUI
```
This script automatically checks and clones all 11 required custom nodes (such as `ComfyUI-GGUF`, `rgthree-comfy`, `ANIMA_BOOSTER`, `ComfyUI-KJNodes`, etc.).

### 3. Check & Download Model Weights
Run the model validator to inspect local weights:
```bash
python scripts/download_models.py --models-dir /path/to/ComfyUI/models
```
The script will output exact `huggingface-cli` download commands for any missing files.

#### Core Model Reference:
- **Qwen-Image 2.1 Engine**:
  - Diffusion UNet: `qwen-image-2.1-Q4_K_M.gguf` (`city96/Qwen-Image-2.1-GGUF`)
  - Text Encoder: `qwen3vl_8b_int8_convrot.safetensors` (`Comfy-Org/Qwen-Image-2.1-GGUF`)
  - VAE: `qwen_image_2.1_vae_bf16.safetensors` (`Comfy-Org/Qwen-Image-2.1-GGUF`)
- **Anima Yuri Engine**:
  - Checkpoint: `miaomiaoHarem_animaBase.safetensors` or `Anima-2.9B-preview-v1.safetensors`
  - Text Encoder: `qwen_3_06b_base.safetensors`
  - VAE: `qwen_image_vae.safetensors`
  - Core LoRAs: `RealSkin`, `aesthetic`, `detailer`, `Scenery_enchancer`, `darklight`, `colorfix`
- **Agent LLM Planner**:
  - `Qwen3.8-27B-Heretic-Ara-iq4_xs-3.0-mtp.gguf` (or any OpenAI-compatible server such as llama.cpp, Ollama, LM Studio)

### 4. Configure `config.json`
Copy `config.example.json` to `config.json` and adjust endpoints and paths:
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

### 5. Launch the Studio
```bash
python web_gui.py
```
Open **[http://127.0.0.1:7860](http://127.0.0.1:7860)** in your browser.

---

## 🎨 Included Workflow Templates

All templates reside in the `workflows/` directory:
- **`qwen-image-2.1-t2i-template.json`**: Clean Text-to-Image API graph. Prompt and aspect ratio are dynamically injected by the LLM agent.
- **`qwen-image-2.1-i2i-template.json`**: Clean Image-to-Image / local editing API graph with reference image latent conditioning.
- **`anima-yuri-aio-template.json`**: Clean SDXL anime generation API graph with dynamic LoRA stack.
- **`reference-sevnfading-advanced.json`**: Full original UI canvas layout of the SevnFading Advanced workflow for inspection in the ComfyUI web UI.

---

# 🌸 中文文档 (Chinese Documentation)

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

## 🤖 交给 AI Agent 一键部署

向你的 AI 编程助手发送：

> **“请读取本项目中的 [AGENT_INSTRUCTIONS.md](./AGENT_INSTRUCTIONS.md)，帮我在本地自动检查并安装所需的 ComfyUI 节点，校验模型与 LoRA，配置好 config.json 并启动 Image Agent Studio。”**

---

## 🛠️ 人工部署步骤

### 1. 克隆与安装依赖
```bash
git clone https://github.com/G0K0U/Image-Agent-Studio.git
cd Image-Agent-Studio
pip install -r requirements.txt
```

### 2. 自动安装 ComfyUI 节点
```bash
python scripts/setup_environment.py --comfy-dir /path/to/ComfyUI
```

### 3. 校验并下载模型
```bash
python scripts/download_models.py --models-dir /path/to/ComfyUI/models
```

### 4. 复制并调整配置文件
复制 `config.example.json` 为 `config.json` 并根据本地环境调整配置。

### 5. 启动控制台
```bash
python web_gui.py
```
访问：**[http://127.0.0.1:7860](http://127.0.0.1:7860)**。

---

## 📜 许可证 (License)

MIT License.
