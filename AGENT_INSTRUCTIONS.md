# 🤖 Agent Deployment Guide (交给 AI Agent 一键部署说明书)

This document is specifically crafted for **Autonomous AI Coding Agents** (such as Claude Code, Google Antigravity, OpenAI Codex, Cursor, RooCode).

When a user provides this repository and asks you to:
> *"Deploy this repo, install all required ComfyUI nodes, download models and LoRAs, configure the LLM prompt planner, and start Anima Agent Studio."*

Follow the exact automated execution playbook below.

---

## 📋 Execution Playbook for AI Agents (English)

### Step 1: Detect ComfyUI & Setup Custom Nodes
Run the automated environment installer:
```bash
python scripts/setup_environment.py --comfy-dir <path_to_comfyui>
```
*If `--comfy-dir` is omitted, the script automatically searches standard parent and sibling folders.*

**What this step does:**
- Verifies Python dependencies (`pip install -r requirements.txt`).
- Clones all 11 required custom nodes directly into `<ComfyUI>/custom_nodes/`:
  - `ComfyUI-GGUF` (for GGUF UNet loading)
  - `rgthree-comfy` (for Context and Power LoRA Loader)
  - `ComfyUI-Impact-Pack` (switches and image logic)
  - `ComfyUI-KJNodes` (KJ utility nodes)
  - `ComfyUI-Custom-Scripts` (resolution selector)
  - `ComfyUI-Logic` (Boolean/String/Int primitives)
  - `ComfyUI-Crystools` (switching & monitoring)
  - `ANIMA_BOOSTER` (Anima Booster & TeaCache)
  - `Anima-Artist-Mixer` (Anima artist packs)
  - `ComfyUI-Anima-LLLite` (Anima LLLite support)
  - `WeiLin-Comfyui-Tools` (LoRA stack interface)
- Generates `config.json` linked to your ComfyUI directories.

---

### Step 2: Verify & Download Weights and LoRAs
Inspect the local models directory against the manifest:
```bash
python scripts/download_models.py --models-dir <path_to_comfyui/models>
```

#### Core Required Weights:
1. **Qwen-Image 2.1 Engine**:
   - `diffusion_models/qwen-image-2.1-Q4_K_M.gguf`
     - Download: `huggingface-cli download city96/Qwen-Image-2.1-GGUF qwen-image-2.1-Q4_K_M.gguf --local-dir <comfy_dir>/models/diffusion_models`
   - `text_encoders/qwen3vl_8b_int8_convrot.safetensors`
     - Download: `huggingface-cli download Comfy-Org/Qwen-Image-2.1-GGUF split_files/text_encoders/qwen3vl_8b_int8_convrot.safetensors --local-dir <comfy_dir>/models/text_encoders`
   - `vae/qwen_image_2.1_vae_bf16.safetensors`
     - Download: `huggingface-cli download Comfy-Org/Qwen-Image-2.1-GGUF split_files/vae/qwen_image_2.1_vae_bf16.safetensors --local-dir <comfy_dir>/models/vae`

2. **Anima AIO Yuri Engine**:
   - `diffusion_models/Anima/miaomiaoHarem_animaBase.safetensors` (or `Anima-2.9B-preview-v1.safetensors`)
   - `text_encoders/qwen_3_06b_base.safetensors`
   - `vae/qwen_image_vae.safetensors`
   - **Recommended LoRA Stack** in `<comfy_dir>/models/loras/`:
     - `Scenery_enchancer-Anima-P3.safetensors` (Scenery & Lighting)
     - `bakaE79AAEE882A4.Md2S.safetensors` (RealSkin texture)
     - `Anima-写实光.safetensors` (Darklight & contrast)
     - `anima_context_detailer_base10.safetensors` (Anatomy detailer)
     - `anima-highres-aesthetic-boost.safetensors` (Aesthetic booster)
     - `Anima_colorfix_v1_by_Volnovik.safetensors` (Colorfix)

---

### Step 3: Configure Local LLM Prompt Agent (VRAM Handover)
Anima Agent Studio supports two modes for prompt planning:

#### Option A: External OpenAI-compatible Endpoint (Default & Easiest)
If user has Ollama, vLLM, LM Studio, or a running `llama-server`:
Edit `config.json`:
```json
{
  "heretic_api_url": "http://127.0.0.1:18200/v1/chat/completions",
  "heretic_model_name": "Qwen3.8-27B-Heretic-Ara-iq4_xs-3.0-mtp.gguf"
}
```

#### Option B: Automated On-Demand VRAM Handover (Recommended for 16GB GPUs)
For single-GPU machines (e.g. RTX 4080 16GB), the agent automatically boots the local LLM with a 4K context, writes parameters, and **immediately unloads** before ComfyUI renders.
Configure `config.json`:
```json
{
  "heretic_runtime_exe": "C:/path/to/llama-server.exe",
  "heretic_model_path": "C:/path/to/Qwen3.8-27B-Heretic-Ara-iq4_xs-3.0-mtp.gguf",
  "heretic_ctx_size": 4096,
  "heretic_gpu_layers": 99
}
```

---

### Step 4: Launch & Verification
1. Start ComfyUI:
   Ensure ComfyUI is running on `http://127.0.0.1:8191`.
2. Start Studio:
   ```bash
   python web_gui.py
   ```
   Open `http://127.0.0.1:7860`.
3. Perform Smoke Test:
   - Make a test POST request to `http://127.0.0.1:7860/api/chat` with:
     ```json
     {"workflow": "qwen", "instruction": "A serene anime girl reading a book under a cherry blossom tree"}
     ```
   - Make a test POST request to `http://127.0.0.1:7860/api/generate` with `{"workflow": "qwen"}`.
   - Confirm status returns `"success"` and returns a valid image URL.

---

# 🇨🇳 中文部署操作指南 (Chinese Version)

本指南专为自主 AI 编程智能体（Claude Code, Antigravity, Codex, Cursor, RooCode 等）设计。

当用户要求部署本项目时，请按照以下标准化流程执行：

### 步骤 1：探测 ComfyUI 环境并安装节点
```bash
python scripts/setup_environment.py --comfy-dir <ComfyUI路径>
```
脚本会自动探测或指定 ComfyUI 根目录，并将 11 个必需节点克隆到 `custom_nodes/` 下，同时生成 `config.json`。

### 步骤 2：校验并下载模型与 LoRA 权重
```bash
python scripts/download_models.py --models-dir <ComfyUI/models路径>
```
根据输出的 `huggingface-cli` 命令下载缺失的模型。

### 步骤 3：配置提示词 LLM 大模型（显存接力）
- 若已有运行中的本地/远程 OpenAI 兼容接口，配置 `heretic_api_url` 即可。
- 若为 RTX 4080 (16GB) 单卡，建议配置 `heretic_runtime_exe` 与 `heretic_model_path`，启用全自动显存接力（推理完成后秒卸载，不抢 ComfyUI 显存）。

### 步骤 4：启动与端到端验证
1. 启动 ComfyUI 确保监听 `http://127.0.0.1:8191`。
2. 运行 `python web_gui.py` 启动控制台（监听 7860 端口）。
3. 执行文生图 Smoke Test 确认返回渲染成图。
