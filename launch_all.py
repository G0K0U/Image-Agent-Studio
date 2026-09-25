#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
One-click Launcher for Image Agent Studio & ComfyUI Server.
- Checks and starts ComfyUI on port 8191 (minimized)
- Checks and starts Image Agent Studio on port 7860 (minimized)
- Polls ports until fully online
- Automatically opens separate browser windows for both services
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PYTHON_EXE = r"F:\AI\ComfyUI\ComfyUI_windows_portable\python_embeded\python.exe"
QWEN_DIR = r"F:\AI\QwenImage21"
STUDIO_DIR = r"F:\AI\Image-Agent-Studio"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def wait_for_port(port, name, timeout=45):
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            print(f"  [✓] {name} (端口 {port}) 已就绪！")
            return True
        time.sleep(1)
    print(f"  [!] {name} (端口 {port}) 等待超时（{timeout}s）")
    return False

def main():
    print("=" * 70)
    print("  🌸 正在启动 Image Agent Studio 与 ComfyUI...")
    print("=" * 70)

    # Windows StartupInfo to start services minimized
    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 6  # SW_MINIMIZE
        creationflags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP

    # 1. Start ComfyUI on port 8191 if not running
    if not is_port_in_use(8191):
        print("  [1/2] 正在后台启动 ComfyUI 服务 (端口 8191)...")
        comfy_cmd = [
            PYTHON_EXE,
            "run_comfy.py",
            "--port=8191",
            "--disable-auto-launch",
            "--preview-method", "none",
            "--extra-model-paths-config", os.path.join(QWEN_DIR, "extra_model_paths.yaml")
        ]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        try:
            subprocess.Popen(
                comfy_cmd,
                cwd=QWEN_DIR,
                env=env,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
        except Exception as e:
            print(f"  [!] 启动 ComfyUI 失败: {e}")
    else:
        print("  [1/2] ComfyUI 已在运行中 (端口 8191)")

    # 2. Start Studio on port 7860 if not running
    if not is_port_in_use(7860):
        print("  [2/2] 正在后台启动 Image Agent Studio (端口 7860)...")
        studio_cmd = [PYTHON_EXE, "-u", "web_gui.py"]
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        try:
            subprocess.Popen(
                studio_cmd,
                cwd=STUDIO_DIR,
                env=env,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
        except Exception as e:
            print(f"  [!] 启动 Studio 失败: {e}")
    else:
        print("  [2/2] Image Agent Studio 已在运行中 (端口 7860)")

    # 3. Wait for ports
    print("-" * 70)
    print("正在等待服务完全就绪...")
    studio_ready = wait_for_port(7860, "Image Agent Studio", timeout=30)
    comfy_ready = wait_for_port(8191, "ComfyUI 引擎", timeout=45)

    # 4. Open independent browser windows
    print("-" * 70)
    print("正在浏览器中分别打开 Studio 和 ComfyUI 两个独立窗口...")

    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    browser_exe = edge_path if os.path.exists(edge_path) else (chrome_path if os.path.exists(chrome_path) else None)

    urls = ["http://127.0.0.1:7860", "http://127.0.0.1:8191"]

    if browser_exe:
        for url in urls:
            try:
                subprocess.Popen([browser_exe, "--new-window", url])
            except Exception as e:
                print(f"  [!] 打开浏览器窗口失败 ({url}): {e}")
                webbrowser.open_new(url)
            time.sleep(0.5)
    else:
        for url in urls:
            webbrowser.open_new(url)
            time.sleep(0.5)

    print("=" * 70)
    print("  🎉 已成功在浏览器打开两个独立窗口：")
    print("     - Image Agent Studio: http://127.0.0.1:7860")
    print("     - ComfyUI 控制台:    http://127.0.0.1:8191")
    print("=" * 70)
    time.sleep(3)

if __name__ == "__main__":
    main()
