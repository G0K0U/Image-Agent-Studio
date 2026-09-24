#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automated Environment Setup Script for Image Agent Studio
Designed for 1-click execution by AI Agents (Claude Code, Antigravity, Codex) or users.
"""

import os
import sys
import json
import shutil
import argparse
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CUSTOM_NODES = {
    "ComfyUI-GGUF": "https://github.com/leejet/ComfyUI-GGUF.git",
    "rgthree-comfy": "https://github.com/rgthree/rgthree-comfy.git",
    "ComfyUI-Impact-Pack": "https://github.com/ltdrdata/ComfyUI-Impact-Pack.git",
    "ComfyUI-KJNodes": "https://github.com/kijai/ComfyUI-KJNodes.git",
    "ComfyUI-Custom-Scripts": "https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git",
    "ComfyUI-Logic": "https://github.com/theUpsider/ComfyUI-Logic.git",
    "ComfyUI-Crystools": "https://github.com/crystian/ComfyUI-Crystools.git",
    "ANIMA_BOOSTER": "https://github.com/BlackSnowSkill/ANIMA_BOOSTER.git",
    "Anima-Artist-Mixer": "https://github.com/An1X3R/Anima-Artist-Mixer.git",
    "ComfyUI-Anima-LLLite": "https://github.com/kohya-ss/ComfyUI-Anima-LLLite.git",
    "WeiLin-Comfyui-Tools": "https://github.com/weilin9999/WeiLin-Comfyui-Tools.git"
}

def find_comfyui(custom_path=None):
    if custom_path and os.path.exists(custom_path):
        return os.path.abspath(custom_path)

    candidates = [
        os.path.join(REPO_ROOT, "ComfyUI"),
        os.path.join(REPO_ROOT, "..", "ComfyUI"),
        os.path.join(REPO_ROOT, "..", "QwenImage21", "ComfyUI"),
        r"F:\AI\QwenImage21\ComfyUI",
        r"F:\AI\ComfyUI\ComfyUI_windows_portable\ComfyUI",
        r"C:\AI\ComfyUI",
    ]
    for c in candidates:
        if os.path.exists(c) and (os.path.exists(os.path.join(c, "main.py")) or os.path.exists(os.path.join(c, "custom_nodes"))):
            return os.path.abspath(c)
    return None

def install_custom_nodes(comfy_dir):
    nodes_dir = os.path.join(comfy_dir, "custom_nodes")
    if not os.path.exists(nodes_dir):
        os.makedirs(nodes_dir, exist_ok=True)

    print(f"\n[1/3] Checking ComfyUI Custom Nodes in: {nodes_dir}")
    for name, git_url in CUSTOM_NODES.items():
        target = os.path.join(nodes_dir, name)
        if os.path.exists(target):
            print(f"  ✓ {name} already installed.")
        else:
            print(f"  ⬇️ Cloning {name} from {git_url}...")
            try:
                subprocess.run(["git", "clone", "--depth", "1", git_url, target], check=True)
                print(f"  ✓ {name} installed successfully.")
                req_file = os.path.join(target, "requirements.txt")
                if os.path.exists(req_file):
                    print(f"    Installing dependencies for {name}...")
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"], check=False)
            except Exception as e:
                print(f"  ❌ Error cloning {name}: {e}")

def create_config(comfy_dir):
    config_file = os.path.join(REPO_ROOT, "config.json")
    example_file = os.path.join(REPO_ROOT, "config.example.json")
    
    cfg = {}
    if os.path.exists(example_file):
        with open(example_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)

    if comfy_dir:
        cfg["comfy_input_dir"] = os.path.normpath(os.path.join(comfy_dir, "input"))
        cfg["comfy_output_dir"] = os.path.normpath(os.path.join(comfy_dir, "output"))

    if not os.path.exists(config_file):
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        print(f"\n[2/3] Generated config.json linked to: {comfy_dir}")
    else:
        print(f"\n[2/3] config.json already exists.")

def main():
    parser = argparse.ArgumentParser(description="Image Agent Studio Environment Setup")
    parser.add_argument("--comfy-dir", help="Path to your ComfyUI root directory")
    args = parser.parse_args()

    print("==================================================")
    print(" 🚀 Image Agent Studio: 1-Click Environment Setup")
    print("==================================================")

    comfy_dir = find_comfyui(args.comfy_dir)
    if comfy_dir:
        print(f"Detected ComfyUI at: {comfy_dir}")
        install_custom_nodes(comfy_dir)
        create_config(comfy_dir)
    else:
        print("⚠️ Could not automatically locate ComfyUI.")
        print("Please run: python scripts/setup_environment.py --comfy-dir /path/to/ComfyUI")
        create_config(None)

    print("\n[3/3] Next steps:")
    print("  1. Run `python scripts/download_models.py` to inspect and download required weights & LoRAs.")
    print("  2. Start ComfyUI on port 8191 (or configure `comfy_api_url` in config.json).")
    print("  3. Start Image Agent Studio: `python web_gui.py`.")
    print("==================================================")

if __name__ == "__main__":
    main()
