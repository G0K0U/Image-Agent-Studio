#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image Agent Bridge: Uses Local LLM (e.g., Heretic Qwen 3.8 27B / llama.cpp / Ollama)
to plan prompts and parameters with automatic VRAM handover.

Supports dual workflow modes:
  1. Qwen-Image 2.1 Advanced (T2I / I2I with official Alibaba natural language expansion & attribute disentanglement)
  2. Anima AIO Yuri (SDXL + LoRA Stack, Danbooru tag-based)
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import time
import base64
import random
import subprocess
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_config():
    config_path = os.path.join(SCRIPT_DIR, "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(SCRIPT_DIR, "config.example.json")
    
    cfg = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            print(f"[Bridge] Warning: Failed to load {config_path}: {e}")
            
    def resolve_path(p, default):
        raw = cfg.get(p, default)
        if not raw:
            return ""
        if os.path.isabs(raw):
            return raw
        return os.path.normpath(os.path.join(SCRIPT_DIR, raw))

    return {
        "comfy_api_url": cfg.get("comfy_api_url", "http://127.0.0.1:8191"),
        "comfy_input_dir": resolve_path("comfy_input_dir", "./ComfyUI/input"),
        "comfy_output_dir": resolve_path("comfy_output_dir", "./ComfyUI/output"),
        "studio_port": cfg.get("studio_port", 7860),
        "heretic_api_url": cfg.get("heretic_api_url", "http://127.0.0.1:18200/v1/chat/completions"),
        "heretic_model_name": cfg.get("heretic_model_name", "Qwen3.8-27B-Heretic-Ara-iq4_xs-3.0-mtp.gguf"),
        "heretic_runtime_exe": resolve_path("heretic_runtime_exe", ""),
        "heretic_model_path": resolve_path("heretic_model_path", ""),
        "heretic_mmproj_path": resolve_path("heretic_mmproj_path", ""),
        "heretic_threads": cfg.get("heretic_threads", 8),
        "heretic_ctx_size": cfg.get("heretic_ctx_size", 4096),
        "heretic_gpu_layers": cfg.get("heretic_gpu_layers", 99),
        "qwen_t2i_workflow": resolve_path("qwen_t2i_workflow", "workflows/qwen-image-2.1-t2i-template.json"),
        "qwen_i2i_workflow": resolve_path("qwen_i2i_workflow", "workflows/qwen-image-2.1-i2i-template.json"),
        "anima_workflow": resolve_path("anima_workflow", "workflows/anima-yuri-aio-template.json")
    }

CONFIG = get_config()

WH_RATIO_MAP = {
    "1:1": (1024, 1024),
    "2:3": (832, 1216),
    "3:2": (1216, 832),
    "3:4": (896, 1152),
    "4:3": (1152, 896),
    "9:16": (768, 1344),
    "16:9": (1344, 768),
    "21:9": (1536, 640),
    "9:21": (640, 1536),
    "1:2": (704, 1408),
    "2:1": (1408, 704),
}

def free_comfyui():
    cfg = get_config()
    comfy_api = cfg["comfy_api_url"]
    try:
        req = urllib.request.Request(
            f"{comfy_api}/free",
            data=json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
        print("[Bridge] ComfyUI VRAM freed.")
    except Exception as e:
        print("[Bridge] Note: ComfyUI /free not reached or skipped:", e)

def kill_heretic():
    cfg = get_config()
    exe = cfg["heretic_runtime_exe"]
    if not exe or not os.path.exists(exe):
        return

    exe_name = os.path.splitext(os.path.basename(exe))[0]
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["powershell", "-Command", f"Get-Process -Name '{exe_name}' -ErrorAction SilentlyContinue | Stop-Process -Force"],
                capture_output=True,
                timeout=10
            )
        else:
            subprocess.run(["pkill", "-f", exe_name], capture_output=True, timeout=10)
    except Exception as e:
        print("[Bridge] Error killing local LLM process:", e)

def start_heretic():
    cfg = get_config()
    exe = cfg["heretic_runtime_exe"]
    model = cfg["heretic_model_path"]
    
    # If no local runtime is configured, assume external server is running
    if not exe or not os.path.exists(exe) or not model or not os.path.exists(model):
        print("[Bridge] No local runtime executable configured. Relying on standing LLM endpoint:", cfg["heretic_api_url"])
        return

    kill_heretic()
    free_comfyui()

    cmd = [
        exe,
        "-m", model,
        "-c", str(cfg["heretic_ctx_size"]),
        "-ngl", str(cfg["heretic_gpu_layers"]),
        "-t", str(cfg["heretic_threads"]),
        "--host", "127.0.0.1",
        "--port", "18200"
    ]
    if cfg["heretic_mmproj_path"] and os.path.exists(cfg["heretic_mmproj_path"]):
        cmd.extend(["--mmproj", cfg["heretic_mmproj_path"], "--no-mmproj-offload"])

    print(f"[Bridge] Starting local LLM server: {' '.join(cmd)}")
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    # Wait for server readiness
    deadline = time.time() + 30
    ready = False
    while time.time() < deadline:
        time.sleep(1)
        try:
            req = urllib.request.urlopen("http://127.0.0.1:18200/health", timeout=2)
            if req.status == 200:
                ready = True
                break
        except Exception:
            pass

    if ready:
        print("[Bridge] Local LLM Server is online!")
    else:
        print("[Bridge] Warning: Local LLM health check timed out, proceeding anyway...")

def query_heretic(instruction, image_path=None, workflow="qwen"):
    cfg = get_config()
    api_url = cfg["heretic_api_url"]
    model_name = cfg["heretic_model_name"]
    
    user_content = []
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/{ext};base64,{b64}"}
        })

    if workflow == "qwen":
        prompts_dir = os.path.join(SCRIPT_DIR, "prompts")
        if image_path:
            p_file = os.path.join(prompts_dir, "system_prompt_edit.txt")
            if os.path.exists(p_file):
                with open(p_file, "r", encoding="utf-8") as f:
                    sys_prompt = f.read()
            else:
                sys_prompt = "You are an expert Qwen-Image 2.1 image editing assistant. Generate attribute disentanglement instructions in JSON format."
        else:
            p_file = os.path.join(prompts_dir, "system_prompt_t2i.txt")
            if os.path.exists(p_file):
                with open(p_file, "r", encoding="utf-8") as f:
                    sys_prompt = f.read()
            else:
                sys_prompt = "You are an expert Qwen-Image 2.1 prompt rewriting assistant. Expand user instructions into high-quality descriptive prompts in JSON format."

        sys_prompt += (
            "\n\n【OUTPUT FORMAT REQUIREMENT】:\n"
            "You MUST output ONLY a valid JSON markdown codeblock conforming to this schema:\n"
            "```json\n"
            "{\n"
            '  "rewritten_prompt": "Descriptive expanded prompt paragraph here...",\n'
            '  "wh_ratio": "2:3",\n'
            '  "steps": 40,\n'
            '  "cfg": 1.0,\n'
            '  "seed": -1\n'
            "}\n"
            "```\n"
            "Output strictly the JSON codeblock without conversational filler."
        )
    else:
        # Anima AIO Yuri
        sys_prompt = (
            "你是一个精通 Stable Diffusion 和 Anima 工作流的顶级智能生图专家 Agent。\n"
            "你的任务是深入解析用户的自然语言指令（以及可选的参考图），输出标准 JSON 格式的工作流参数配置。\n\n"
            "【本地已安装 Anima 核心 LoRA 对应库】：\n"
            "- RealSkin (权重 0.8): 真实皮肤、毛孔细腻、写实人体\n"
            "- aesthetic (权重 0.35): 画质增强、超清、美学提升\n"
            "- detailer (权重 0.4): 细节丰富、毛发与纹理刻画\n"
            "- Scenery_enchancer (权重 0.7): 唯美风景、自然光照\n"
            "- darklight (权重 0.65): 暗黑风、深邃阴影、高对比度\n\n"
            "【严格要求】：\n"
            "1. 如果有参考图，正向提示词 (prompt) 必须准确识别并保留原图中的角色特征（如角色名、发色发型、眼眸、衣着配饰、躺卧或站立姿势构图等），并精准融合用户指令的改动。\n"
            "2. 负向提示词 (negative_prompt) 必须加入对修改前状态的否定。\n"
            "3. 输出必须是合法 JSON 字符串，包含以下键：\n"
            "```json\n"
            "{\n"
            '  "prompt": "(masterpiece, best quality, absurdres:1.2), ...",\n'
            '  "negative_prompt": "(worst quality, low quality:1.4), ...",\n'
            '  "steps": 28,\n'
            '  "cfg": 4.0,\n'
            '  "denoise": 0.55,\n'
            '  "seed": -1,\n'
            '  "enable_lora": "RealSkin,aesthetic,detailer",\n'
            '  "strength": 0.5\n'
            "}\n"
            "```\n"
            "只输出 JSON 代码块，绝不要输出额外开场白或解释。"
        )

    user_content.append({
        "type": "text",
        "text": f"用户指令：{instruction}\n请根据指令（及参考图）规划完整的参数，直接输出 JSON。"
    })

    req_body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2,
        "max_tokens": 1024
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    res = urllib.request.urlopen(req, timeout=90)
    data = json.loads(res.read())
    raw_content = data["choices"][0]["message"]["content"]

    json_text = raw_content.strip()
    if "```json" in json_text:
        json_text = json_text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in json_text:
        json_text = json_text.split("```", 1)[1].split("```", 1)[0].strip()
    return json.loads(json_text)

def apply_to_qwen_workflow(params, saved_image_filename=None):
    cfg = get_config()
    is_i2i = bool(saved_image_filename)
    target_path = cfg["qwen_i2i_workflow"] if is_i2i else cfg["qwen_t2i_workflow"]
    
    with open(target_path, "r", encoding="utf-8") as f:
        graph = json.load(f)
        
    rewritten_prompt = params.get("rewritten_prompt") or params.get("prompt", "")
    wh_ratio = params.get("wh_ratio", "2:3" if is_i2i else "16:9")
    w, h = WH_RATIO_MAP.get(wh_ratio, (832, 1216) if is_i2i else (1344, 768))
    
    # 4: TextEncodeQwenImage21
    if "4" in graph:
        graph["4"]["inputs"]["prompt"] = rewritten_prompt
        if is_i2i and saved_image_filename:
            graph["4"]["inputs"]["images.image_1"] = ["9", 0]
            
    # 5: EmptyLatentImage
    if "5" in graph:
        graph["5"]["inputs"]["width"] = w
        graph["5"]["inputs"]["height"] = h
        
    # 6: KSampler
    if "6" in graph:
        ks = graph["6"]["inputs"]
        ks["steps"] = int(params.get("steps", 40))
        ks["cfg"] = float(params.get("cfg", 1.0))
        s = int(params.get("seed", -1))
        ks["seed"] = random.randint(1, 10**15) if s == -1 else s
        
    # 9: LoadImage (for i2i)
    if is_i2i and "9" in graph and saved_image_filename:
        graph["9"]["inputs"]["image"] = saved_image_filename
        
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"[Bridge] Qwen workflow updated: {target_path} (wh_ratio: {wh_ratio}, {w}x{h})")
    return target_path

def apply_to_anima_workflow(params, saved_image_filename=None):
    cfg = get_config()
    target_path = cfg["anima_workflow"]
    
    with open(target_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    # 1610: Positive Prompt
    if "1610" in graph and "prompt" in params:
        graph["1610"]["inputs"]["value"] = params["prompt"]

    # 1611: Negative Prompt
    if "1611" in graph and "negative_prompt" in params:
        graph["1611"]["inputs"]["value"] = params["negative_prompt"]

    # 118: KSampler
    if "118" in graph:
        ks = graph["118"]["inputs"]
        if "steps" in params:
            ks["steps"] = int(params["steps"])
        if "cfg" in params:
            ks["cfg"] = float(params["cfg"])
        if "denoise" in params:
            ks["denoise"] = float(params["denoise"])
        s = int(params.get("seed", -1))
        ks["seed"] = random.randint(1, 10**15) if s == -1 else s

    # 1608: LoadImage
    if saved_image_filename and "1608" in graph:
        graph["1608"]["inputs"]["image"] = saved_image_filename

    # LoRA Stacking
    lora_targets = [l.strip().lower() for l in params.get("enable_lora", "").split(",") if l.strip()]
    default_strength = float(params.get("strength", 0.5))

    for nid in ["1381", "1382", "1383", "1384", "1697"]:
        if nid in graph:
            inputs = graph[nid].get("inputs", {})
            for k, v in inputs.items():
                if isinstance(v, dict) and "lora" in v:
                    lora_name = os.path.basename(v["lora"]).lower()
                    matched = False
                    for target in lora_targets:
                        if target in lora_name:
                            matched = True
                            break
                    if matched:
                        v["on"] = True
                        if default_strength > 0:
                            v["strength"] = default_strength
                    elif len(lora_targets) > 0:
                        v["on"] = False

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"[Bridge] Anima workflow updated: {target_path}")
    return target_path
