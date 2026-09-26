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
import re
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
        "heretic_api_url": cfg.get("heretic_api_url", "http://127.0.0.1:18205/v1/chat/completions"),
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

def get_heretic_port(cfg=None):
    if cfg is None:
        cfg = get_config()
    url = cfg.get("heretic_api_url", "")
    try:
        from urllib.parse import urlparse
        p = urlparse(url).port
        if p:
            return p
    except Exception:
        pass
    return 18205

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
    "3:1": (1536, 512),
    "1:3": (512, 1536),
    "5:7": (864, 1208),
    "7:5": (1208, 864),
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
    port = get_heretic_port(cfg)

    # 1. Kill any process listening on our Studio LLM port (e.g. 18205)
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["powershell", "-Command", f"$p = (Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess; if ($p) {{ Stop-Process -Id $p -Force }}"],
                capture_output=True,
                timeout=5
            )
    except Exception as e:
        print(f"[Bridge] Error releasing port {port}:", e)

    # 2. Terminate local LLM processes
    if exe and os.path.exists(exe):
        exe_name = os.path.splitext(os.path.basename(exe))[0]
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["powershell", "-Command", f"Get-Process -Name '{exe_name}','llama-kvmem-server','llama-server' -ErrorAction SilentlyContinue | Stop-Process -Force"],
                    capture_output=True,
                    timeout=5
                )
            else:
                subprocess.run(["pkill", "-f", exe_name], capture_output=True, timeout=5)
        except Exception as e:
            print("[Bridge] Error killing local LLM process:", e)

    # 3. Release any ninfer-serve process occupying GPU memory
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["powershell", "-Command", "Get-Process -Name 'ninfer-serve' -ErrorAction SilentlyContinue | Stop-Process -Force"],
                capture_output=True,
                timeout=5
            )
    except Exception as e:
        pass

def start_heretic():
    cfg = get_config()
    exe = cfg["heretic_runtime_exe"]
    model = cfg["heretic_model_path"]
    port = get_heretic_port(cfg)
    
    # If no local runtime is configured, assume external server is running
    if not exe or not os.path.exists(exe) or not model or not os.path.exists(model):
        print("[Bridge] No local runtime executable configured. Relying on standing LLM endpoint:", cfg["heretic_api_url"])
        return

    kill_heretic()
    free_comfyui()

    exe_name = os.path.basename(exe).lower()
    is_kvmem = "kvmem" in exe_name

    cmd = [
        exe,
        "-m", model,
        "-c", str(cfg.get("heretic_ctx_size", 8192)),
        "-n", "1024",
        "-ngl", str(cfg.get("heretic_gpu_layers", 99)),
        "--host", "127.0.0.1",
        "--port", str(port),
        "--no-ui"
    ]
    
    if cfg.get("heretic_model_name"):
        cmd.extend(["-a", cfg["heretic_model_name"]])

    if is_kvmem:
        cmd.extend(["--kvmem-gen-reserve", "1024"])
    elif cfg.get("heretic_threads"):
        cmd.extend(["-t", str(cfg["heretic_threads"])])

    if cfg.get("heretic_mmproj_path") and os.path.exists(cfg["heretic_mmproj_path"]):
        cmd.extend(["--mmproj", cfg["heretic_mmproj_path"], "--mmproj-offload"])

    print(f"[Bridge] Starting local LLM server on port {port}: {' '.join(cmd)}")
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    # Wait for server readiness (model loading takes ~10-15s)
    deadline = time.time() + 60
    ready = False
    health_url = f"http://127.0.0.1:{port}/health"
    while time.time() < deadline:
        time.sleep(1)
        try:
            req = urllib.request.urlopen(health_url, timeout=2)
            if req.status == 200:
                ready = True
                break
        except Exception:
            pass

    if ready:
        print(f"[Bridge] Local LLM Server on port {port} is online!")
    else:
        print(f"[Bridge] Warning: Local LLM health check on port {port} timed out, proceeding anyway...")

def query_heretic(instruction, image_path=None, workflow="qwen"):
    cfg = get_config()
    api_url = cfg["heretic_api_url"]
    model_name = cfg["heretic_model_name"]
    exe_name = os.path.basename(cfg.get("heretic_runtime_exe", "")).lower()
    is_kvmem = "kvmem" in exe_name
    
    user_content = []
    if image_path and os.path.exists(image_path):
        b64 = None
        try:
            from PIL import Image
            import io
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                w, h = img.size
                max_dim = 768
                if max(w, h) > max_dim:
                    scale = max_dim / max(w, h)
                    img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as e:
            print("[Bridge] Image resizing fallback to raw:", e)
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")

        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        })

    if workflow == "qwen":
        skill_dir = os.path.join(SCRIPT_DIR, "skills", "qwen-image-2-1-prompter")
        ref_dir = os.path.join(skill_dir, "references")
        
        cheat_sheet = ""
        cs_file = os.path.join(ref_dir, "cheat_sheet.md")
        if os.path.exists(cs_file):
            with open(cs_file, "r", encoding="utf-8") as f:
                cheat_sheet = f.read()

        if image_path:
            # Mode 2: Image Edit & Multi-Image Compositing (Attribute Disentanglement)
            p_file = os.path.join(ref_dir, "edit_rules.md")
            if not os.path.exists(p_file):
                p_file = os.path.join(SCRIPT_DIR, "prompts", "system_prompt_edit.txt")
            with open(p_file, "r", encoding="utf-8") as f:
                sys_prompt = f.read()
            if cheat_sheet:
                sys_prompt += f"\n\n---\n## Parameter & Vocabulary Reference\n{cheat_sheet}"
        else:
            # Mode 1: Text-to-Image (T2I) (8-step observer prose)
            p_file = os.path.join(ref_dir, "t2i_rules.md")
            if not os.path.exists(p_file):
                p_file = os.path.join(SCRIPT_DIR, "prompts", "system_prompt_t2i.txt")
            with open(p_file, "r", encoding="utf-8") as f:
                sys_prompt = f.read()
            if cheat_sheet:
                sys_prompt += f"\n\n---\n## Parameter & Vocabulary Reference\n{cheat_sheet}"

        sys_prompt += (
            "\n\n【OUTPUT FORMAT REQUIREMENT (API / Pipeline Mode)】:\n"
            "You MUST output ONLY a valid JSON markdown codeblock conforming to this schema:\n"
            "```json\n"
            "{\n"
            '  "rewritten_prompt": "Descriptive expanded prompt paragraph here...",\n'
            '  "wh_ratio": "2:3",\n'
            '  "ratio_follow": "",\n'
            '  "steps": 40,\n'
            '  "cfg": 1.0,\n'
            '  "seed": -1\n'
            "}\n"
            "```\n"
            "Notes on fields:\n"
            "- 'rewritten_prompt': exactly one continuous descriptive paragraph, no newline characters, balanced straight quotes.\n"
            "- 'wh_ratio': e.g. '16:9', '2:3', '1:1', '3:2'. For edit mode, if following input image ratio, set 'wh_ratio': '' and 'ratio_follow': '<image1>'.\n"
            "Output strictly the JSON codeblock without conversational filler."
        )
    else:
        # Anima AIO Yuri
        sys_prompt = (
            "你是一个精通 Stable Diffusion 和 Anima 工作流的顶级智能生图专家 Agent。\n"
            "你的任务是深入解析用户的自然语言指令（以及可选的参考图），精确规划画风、提示词、LoRA 及参数配置。\n\n"
            "【本地已配置的 Anima 核心 LoRA 对应库及作用】：\n"
            "- semi_realistic / 半写实 (推荐权重 0.70-0.75): 半写实动漫风格，精美逼真立体光影，细腻CG质感。当用户提到“半写实”、“写实画风”、“厚涂写实”、“逼真质感”、“立体感”时必须启用！\n"
            "- RealSkin / 真实皮肤 (推荐权重 0.50): 真实皮肤微质感、毛孔细腻度与真实人体光泽。可与半写实 LoRA 叠加增强质感。\n"
            "- leg_detail / 腿部质感 (推荐权重 0.55): 黑丝、连裤袜织物细节、腿部曲线与丝袜光泽强化。当提到“黑丝/丝袜/腿部/足部”时启用！\n"
            "- aesthetic (推荐权重 0.35): 美学提升、画面超清与色彩通透度（默认常开）。\n"
            "- detailer (推荐权重 0.35): 发丝、瞳孔、五官与配饰高精度微细节刻画（默认常开）。\n"
            "- scenery (推荐权重 0.50): 宏大背景、风景与室外环境光影。\n\n"
            "【画风与提示词规划准则（极其关键）】：\n"
            "1. 画风分支判断 (style_mode: 'semi_realistic' 或 'anime')：\n"
            "   - 若用户指令要求【半写实】、【真实质感】、【写实画风】：\n"
            "     * style_mode 设为 'semi_realistic'。\n"
            "     * loras 必须包含 'semi_realistic': 0.70，并可搭配 'RealSkin': 0.50 与 'detailer': 0.35。\n"
            "     * 正向提示词开头必须写入：`(semi-realistic:1.25), (photorealistic anime illustration:1.15), (masterpiece, best quality, absurdres:1.2), detailed realistic skin texture, realistic soft lighting, subsurface scattering, ambient occlusion`。\n"
            "     * 负向提示词中【绝对严禁】出现 `(realistic, 3d, photo)`！只保留常规劣质过滤词：`(worst quality, low quality:1.4), (bad anatomy, bad hands:1.2), blurry, watermark, extra fingers, deformed face, duplicate`。\n"
            "   - 若用户指令要求【纯二次元/动漫/日系插画】：\n"
            "     * style_mode 设为 'anime'。\n"
            "     * 正向提示词开头写入：`(anime style:1.3), (masterpiece, best quality, absurdres:1.2)`。\n"
            "     * 负向提示词包含：`(worst quality:1.4), (3d, realistic, photo:1.3), bad anatomy, bad hands`。\n"
            "2. 参考图保真度与去噪度 (denoise)：\n"
            "   - 图生图下，必须仔细识别参考图的角色特征（发型发色、五官构图、服饰与黑丝材质），严禁随意更改角色核心特征。\n"
            "   - 保持姿势与特征同时改变画风质感，denoise 建议设为 0.50 - 0.52。\n"
            "3. 输出格式要求：\n"
            "必须输出纯 JSON 代码块，符合以下结构：\n"
            "```json\n"
            "{\n"
            '  "style_mode": "semi_realistic",\n'
            '  "prompt": "(semi-realistic:1.25), (photorealistic anime illustration:1.15), (masterpiece, best quality, absurdres:1.2), 1girl, solo, detailed skin texture, ...",\n'
            '  "negative_prompt": "(worst quality, low quality:1.4), (bad anatomy, bad hands:1.2), blurry, watermark, ...",\n'
            '  "steps": 30,\n'
            '  "cfg": 4.5,\n'
            '  "denoise": 0.50,\n'
            '  "seed": -1,\n'
            '  "loras": {\n'
            '    "semi_realistic": 0.70,\n'
            '    "RealSkin": 0.50,\n'
            '    "aesthetic": 0.35,\n'
            '    "detailer": 0.35\n'
            '  }\n'
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

    try:
        return json.loads(json_text)
    except Exception as je:
        print(f"[Bridge] Warning: JSON decode failed ({je}), attempting repair on:\n{json_text}")
        if not json_text.endswith("}"):
            last_comma = json_text.rfind(",")
            if last_comma != -1:
                try:
                    return json.loads(json_text[:last_comma] + "\n}")
                except Exception:
                    pass
        raise je

def apply_to_qwen_workflow(params, saved_image_filename=None):
    cfg = get_config()
    is_i2i = bool(saved_image_filename)
    target_path = cfg["qwen_i2i_workflow"] if is_i2i else cfg["qwen_t2i_workflow"]
    
    with open(target_path, "r", encoding="utf-8") as f:
        graph = json.load(f)
        
    rewritten_prompt = params.get("rewritten_prompt") or params.get("prompt", "")
    wh_ratio = params.get("wh_ratio", "")
    ratio_follow = params.get("ratio_follow", "")

    if is_i2i and saved_image_filename and (not wh_ratio or ratio_follow):
        try:
            from PIL import Image
            img_full = os.path.join(cfg["comfy_input_dir"], saved_image_filename)
            if os.path.exists(img_full):
                with Image.open(img_full) as im:
                    iw, ih = im.size
                    target_ratio = iw / ih
                    best_r = min(WH_RATIO_MAP.keys(), key=lambda r: abs((WH_RATIO_MAP[r][0] / WH_RATIO_MAP[r][1]) - target_ratio))
                    wh_ratio = best_r
        except Exception:
            wh_ratio = "2:3"
    elif not wh_ratio:
        wh_ratio = "2:3" if is_i2i else "16:9"

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

def clean_negative_prompt_for_realism(neg_prompt):
    cleaned = neg_prompt
    cleaned = re.sub(r'\([^)]*(?:realistic|photo|3d)[^)]*\)[, ]*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b(?:photorealistic|realistic|photo|3d)\b[, ]*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r',\s*,+', ',', cleaned)
    cleaned = re.sub(r'^\s*,\s*', '', cleaned)
    cleaned = re.sub(r'\s*,\s*$', '', cleaned).strip()
    if not cleaned:
        cleaned = "(worst quality, low quality:1.4), (bad anatomy, bad hands:1.2), blurry, watermark, extra fingers, deformed face, duplicate"
    return cleaned

def apply_to_anima_workflow(params, saved_image_filename=None):
    cfg = get_config()
    target_path = cfg["anima_workflow"]
    
    with open(target_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    # 1. Detect style mode: semi-realistic vs pure anime
    p_raw = str(params.get("prompt", "")).lower()
    style_mode = str(params.get("style_mode", "")).lower()
    loras_dict = params.get("loras", {}) if isinstance(params.get("loras"), dict) else {}
    enable_lora_str = str(params.get("enable_lora", "")).lower()

    # Robust multi-layered semi-realistic intent detection
    is_semi = (
        style_mode in ("semi_realistic", "semi-realistic", "realistic") or
        any(k in ("semi_realistic", "semi-realistic", "半写实", "realskin", "真实皮肤") for k in loras_dict.keys()) or
        any(k in enable_lora_str for k in ("semi_realistic", "semi-realistic", "半写实", "realskin", "真实皮肤")) or
        any(k in p_raw for k in ("semi-realistic", "semi_realistic", "photorealistic", "半写实", "写实画风", "厚涂写实"))
    )

    # Stockings / leg texture detection (prevents skin-colored stockings)
    has_stockings = any(k in p_raw for k in ("black pantyhose", "pantyhose", "stockings", "tights", "黑丝", "丝袜", "连裤袜"))

    # 2. Positive Prompt (Node 1610)
    if "1610" in graph and "prompt" in params:
        p_val = params["prompt"].strip()
        if is_semi:
            # Strip anime style anchors
            p_val = re.sub(r'\([^)]*anime style[^)]*\)[, ]*', '', p_val, flags=re.IGNORECASE)
            p_val = re.sub(r'\banime style\b[, ]*', '', p_val, flags=re.IGNORECASE)
            # Ensure semi-realistic anchor is present
            if "semi-realistic" not in p_val.lower() and "半写实" not in p_val:
                anchor = "(semi-realistic:1.25), (photorealistic anime illustration:1.15), (masterpiece, best quality, absurdres:1.2), detailed realistic skin texture, realistic soft lighting"
                p_val = f"{anchor}, {p_val}" if p_val else anchor
        else:
            if "anime style" not in p_val.lower():
                p_val = "(anime style:1.3), " + p_val
        graph["1610"]["inputs"]["value"] = p_val

    # 3. Negative Prompt (Node 1611)
    if "1611" in graph and "negative_prompt" in params:
        n_val = params["negative_prompt"].strip()
        if is_semi:
            n_val = clean_negative_prompt_for_realism(n_val)
        else:
            if "3d" not in n_val.lower() and "realistic" not in n_val.lower():
                n_val = "(3d, realistic, photo:1.3), " + n_val
        graph["1611"]["inputs"]["value"] = n_val

    # 4. KSampler (Node 118)
    s = int(params.get("seed", -1))
    cur_seed = random.randint(1, 10**15) if s == -1 else s

    if "118" in graph:
        ks = graph["118"]["inputs"]
        if "steps" in params:
            ks["steps"] = int(params["steps"])
        if "cfg" in params:
            ks["cfg"] = float(params["cfg"])
        if "denoise" in params:
            d = float(params["denoise"])
            if saved_image_filename and d > 0.52:
                print(f"[Bridge] Denoise {d} safely clamped to 0.50 to preserve stockings & character fidelity")
                d = 0.50
            ks["denoise"] = d
        ks["seed"] = cur_seed

    # 5. FaceDetailer (Node 1701)
    if "1701" in graph:
        fd = graph["1701"]["inputs"]
        fd["seed"] = cur_seed
        if "face_denoise" in params:
            fd["denoise"] = float(params["face_denoise"])
        elif "denoise" not in fd or fd["denoise"] > 0.35:
            fd["denoise"] = 0.30

    # 6. LoadImage & Mode Switching (Img2Img vs Text2Img)
    if saved_image_filename:
        if "1608" in graph:
            graph["1608"]["inputs"]["image"] = saved_image_filename
        if "1607" in graph:
            graph["1607"]["inputs"]["image"] = saved_image_filename
        if "1603:1525" in graph:
            graph["1603:1525"]["inputs"]["boolean"] = True
        if "1603:1528" in graph:
            graph["1603:1528"]["inputs"]["boolean"] = False
        if "118" in graph and "denoise" not in params:
            graph["118"]["inputs"]["denoise"] = 0.50
    else:
        if "1607" in graph:
            graph["1607"]["inputs"]["image"] = "reference.png"
        if "1608" in graph:
            graph["1608"]["inputs"]["image"] = "reference.png"
        if "1603:1525" in graph:
            graph["1603:1525"]["inputs"]["boolean"] = False
        if "1603:1528" in graph:
            graph["1603:1528"]["inputs"]["boolean"] = True
        if "118" in graph and "denoise" not in params:
            graph["118"]["inputs"]["denoise"] = 1.0

    # 7. LoRA Stacking Management
    req_loras = {}
    for k, v in loras_dict.items():
        try:
            req_loras[str(k).lower()] = float(v)
        except (ValueError, TypeError):
            req_loras[str(k).lower()] = 0.5
    for item in enable_lora_str.split(","):
        t = item.strip().lower()
        if t and t not in req_loras:
            req_loras[t] = 0.5

    # If is_semi is True, ensure semi_realistic and realskin are in req_loras
    if is_semi:
        if "semi_realistic" not in req_loras and "半写实" not in req_loras:
            req_loras["semi_realistic"] = 0.72
        if "realskin" not in req_loras and "真实皮肤" not in req_loras:
            req_loras["realskin"] = 0.50
    if has_stockings:
        if "leg_detail" not in req_loras and "腿部质感" not in req_loras:
            req_loras["leg_detail"] = 0.55

    # Always ensure aesthetic and detailer are active
    if "detailer" not in req_loras:
        req_loras["detailer"] = 0.35
    if "aesthetic" not in req_loras:
        req_loras["aesthetic"] = 0.35

    # Configure Node 1381 (Characters)
    if "1381" in graph:
        for k, v in graph["1381"].get("inputs", {}).items():
            if isinstance(v, dict) and "lora" in v:
                lname = os.path.basename(v["lora"]).lower()
                if "半写实" in lname:
                    v["on"] = False
                else:
                    v["on"] = any(t in lname for t in req_loras)

    # Configure Node 1382 (2D Anime Styles): DISABLE ALL if is_semi
    if "1382" in graph:
        for k, v in graph["1382"].get("inputs", {}).items():
            if isinstance(v, dict) and "lora" in v:
                if is_semi:
                    v["on"] = False
                else:
                    lname = os.path.basename(v["lora"]).lower()
                    v["on"] = any(t in lname for t in req_loras)

    # Configure Node 1383 (Realism & Textures)
    if "1383" in graph:
        for k, v in graph["1383"].get("inputs", {}).items():
            if isinstance(v, dict) and "lora" in v:
                lname = os.path.basename(v["lora"]).lower()
                if "半写实" in lname:
                    v["on"] = is_semi or any(t in ("semi_realistic", "半写实") for t in req_loras)
                    v["strength"] = req_loras.get("semi_realistic", req_loras.get("半写实", 0.72))
                elif "realskin" in lname:
                    v["on"] = is_semi or any(t in ("realskin", "真实皮肤") for t in req_loras)
                    v["strength"] = req_loras.get("realskin", req_loras.get("真实皮肤", 0.50))
                elif "baka" in lname:
                    v["on"] = not is_semi and any(t in ("baka", "动漫皮肤") for t in req_loras)
                    v["strength"] = req_loras.get("baka", 0.45)
                elif "腿部" in lname:
                    v["on"] = has_stockings or any(t in ("leg_detail", "腿部质感", "腿部") for t in req_loras)
                    v["strength"] = req_loras.get("leg_detail", req_loras.get("腿部质感", 0.55))
                elif "scenery" in lname or "background" in lname:
                    v["on"] = any(t in ("scenery", "background", "风景") for t in req_loras)
                    v["strength"] = req_loras.get("scenery", 0.50)
                else:
                    v["on"] = False

    # Configure Node 1384 (Quality & Enhancement)
    if "1384" in graph:
        for k, v in graph["1384"].get("inputs", {}).items():
            if isinstance(v, dict) and "lora" in v:
                lname = os.path.basename(v["lora"]).lower()
                if "detailer" in lname:
                    v["on"] = True
                    v["strength"] = req_loras.get("detailer", 0.35)
                elif "aesthetic" in lname:
                    v["on"] = True
                    v["strength"] = req_loras.get("aesthetic", 0.35)
                elif "colorfix" in lname:
                    v["on"] = any(t in ("colorfix", "色彩修复") for t in req_loras)
                    v["strength"] = req_loras.get("colorfix", 0.30)

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"[Bridge] Anima workflow updated: {target_path} (is_semi={is_semi}, has_stockings={has_stockings})")
    return target_path
