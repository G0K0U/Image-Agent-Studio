#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image Agent Studio: Dual-Workflow Web GUI
Supports:
  1. Qwen-Image 2.1 Advanced (Text-to-Image / Image-to-Image / Local Editing)
  2. Anima AIO Yuri (SDXL Anime Specialization + LoRA Stacking)
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import json
import time
import base64
import random
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

import image_agent_bridge

CONFIG = image_agent_bridge.get_config()

HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Image Agent Studio - Dual-Engine AI Workspace</title>
  <style>
    :root {
      --bg: #0b0d13;
      --card: #151822;
      --border: #232838;
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --accent: #ec4899;
      --accent-hover: #db2777;
      --text: #f8fafc;
      --muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background-color: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; padding: 20px; }
    .container { max-width: 1440px; margin: 0 auto; display: grid; grid-template-columns: 520px 1fr; gap: 20px; }
    header { grid-column: 1 / -1; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }
    h1 { font-size: 22px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; }
    .badges { display: flex; gap: 8px; }
    .badge { font-size: 12px; background: #6366f122; color: #a5b4fc; border: 1px solid #6366f144; padding: 3px 10px; border-radius: 999px; }
    .badge-vram { background: #10b98122; color: #34d399; border-color: #10b98144; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 18px; margin-bottom: 16px; }
    .card-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #f8fafc; display: flex; justify-content: space-between; align-items: center; }
    textarea, input, select { width: 100%; background: #0b0d13; border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: 10px; font-size: 13px; margin-bottom: 10px; font-family: inherit; }
    textarea:focus, input:focus, select:focus { outline: none; border-color: var(--primary); }
    button { width: 100%; background: var(--primary); color: #fff; border: none; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
    button:hover { background: var(--primary-hover); }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-generate { background: var(--accent); margin-top: 10px; font-size: 15px; }
    .btn-generate:hover { background: var(--accent-hover); }
    .param-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
    .param-item label { font-size: 11px; color: var(--muted); display: block; margin-bottom: 4px; }
    .param-item input, .param-item select { margin-bottom: 0; }
    .status-box { background: #0b0d13; border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; max-height: 220px; overflow-y: auto; color: #cbd5e1; }
    .preview-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 620px; background: #0b0d13; border: 2px dashed var(--border); border-radius: 12px; overflow: hidden; position: relative; padding: 12px; }
    .preview-img { max-width: 100%; max-height: 780px; object-fit: contain; border-radius: 8px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); cursor: pointer; }
    .placeholder { color: var(--muted); text-align: center; }
    .spinner { border: 4px solid #232838; border-top: 4px solid var(--primary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 16px; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .thumb-preview { width: 56px; height: 56px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); flex-shrink: 0; }
    .workflow-pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 6px; }
    .pill-qwen { background: #0284c722; color: #38bdf8; border: 1px solid #0284c744; }
    .pill-anima { background: #ec489922; color: #f472b6; border: 1px solid #ec489944; }
    .dropzone { border: 2px dashed var(--border); border-radius: 8px; padding: 12px; text-align: center; background: #0b0d13; cursor: pointer; transition: all 0.2s ease; margin-top: 4px; }
    .dropzone:hover { border-color: var(--primary); background: #10131d; }
    .dropzone.drag-active { border-color: #38bdf8 !important; background: #0284c718 !important; box-shadow: 0 0 16px rgba(56, 189, 248, 0.35); }
    .dropzone-content { display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--muted); font-size: 12px; pointer-events: none; }
    .dropzone-loaded { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🌸 Image Agent Studio <span id="curEnginePill" class="workflow-pill pill-qwen">Qwen-Image 2.1</span></h1>
      <div class="badges">
        <span class="badge">🧠 LLM Agent (Prompt Planner)</span>
        <span class="badge badge-vram">⚡ ComfyUI (100% Dedicated VRAM)</span>
      </div>
    </header>

    <div class="sidebar">
      <div class="card">
        <div class="card-title">🎯 Target Engine / 目标工作流引擎</div>
        <select id="wfSelect" onchange="onWorkflowChange()" style="font-weight: 600; font-size: 13px; color: #38bdf8;">
          <option value="qwen" selected>✨ Qwen-Image 2.1 Advanced (T2I / I2I / Local Edit)</option>
          <option value="anima">🌸 Anima AIO Yuri (SDXL Anime + LoRA Stack)</option>
        </select>

        <div class="card-title" style="margin-top: 14px;">🤖 Prompt Instruction / Vision Edit / 自然语言指令</div>
        <textarea id="instruction" rows="3" placeholder="e.g. A hyper-realistic cyberpunk street with neon reflections, silver-haired anime girl with translucent umbrella, cinematic lighting..."></textarea>
        
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <label style="font-size: 11px; color: var(--muted);">Reference Image / 参考底图 (支持复制粘贴与拖入):</label>
            <span id="refBadge" style="font-size: 10px; color: #10b981; display: none;">● 图生图模式已激活</span>
          </div>
          
          <div id="dropZone" class="dropzone" onclick="document.getElementById('refImage').click()">
            <input type="file" id="refImage" accept="image/*" style="display: none;">
            
            <div id="dropPrompt" class="dropzone-content">
              <svg style="width: 24px; height: 24px; opacity: 0.7; margin-bottom: 2px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              <span>📂 点击选择、<strong>直接拖入图片</strong> 或 <strong>Ctrl+V 粘贴</strong></span>
              <span style="font-size: 11px; color: #64748b;">支持截图工具、浏览器图片直接拖入或剪贴板粘贴</span>
            </div>

            <div id="dropLoaded" class="dropzone-loaded" style="display: none;" onclick="event.stopPropagation();">
              <div style="display: flex; align-items: center; gap: 10px; overflow: hidden;">
                <img id="refThumb" class="thumb-preview" alt="参考底图" style="cursor: pointer;" onclick="window.open(this.src)" title="点击新窗口查看原图">
                <div style="text-align: left; overflow: hidden;">
                  <div id="refImgName" style="font-size: 12px; font-weight: 600; color: #f8fafc; max-width: 230px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">参考图已就绪</div>
                  <div id="refImgSize" style="font-size: 10px; color: var(--muted);">正在读取尺寸...</div>
                </div>
              </div>
              <div style="display: flex; gap: 6px; flex-shrink: 0;">
                <button type="button" onclick="document.getElementById('refImage').click()" style="width: auto; padding: 5px 10px; font-size: 11px; background: #334155;">更换</button>
                <button type="button" id="btnClearImg" onclick="clearImage()" style="width: auto; padding: 5px 10px; font-size: 11px; background: #ef444422; color: #f87171; border: 1px solid #ef444444;">移除</button>
              </div>
            </div>
          </div>
        </div>

        <button id="btnPlan" onclick="sendToAgent()">✨ Plan Workflow with Agent / 智能规划写入</button>
      </div>

      <div class="card">
        <div class="card-title">
          <span>⚙️ Workflow Parameters / 参数控制板</span>
          <button style="width: auto; padding: 2px 8px; font-size: 11px; background: transparent; border: 1px solid var(--border);" onclick="fetchStatus()">Refresh / 刷新</button>
        </div>
        <div class="param-grid">
          <div class="param-item">
            <label>Sampling Steps / 步数</label>
            <input type="number" id="pSteps">
          </div>
          <div class="param-item">
            <label>CFG Scale</label>
            <input type="number" id="pCFG" step="0.1">
          </div>
          <div class="param-item">
            <label id="lblRatioOrDenoise">Aspect Ratio / 画幅比例</label>
            <input type="text" id="pRatioOrDenoise">
          </div>
          <div class="param-item">
            <label>Seed / 随机种子 (-1 = Random)</label>
            <input type="text" id="pSeed">
          </div>
        </div>

        <div style="margin-top: 10px;">
          <label style="font-size: 11px; color: var(--muted); display: block; margin-bottom: 4px;">Positive Prompt / 正向提示词</label>
          <textarea id="pPrompt" rows="4"></textarea>
        </div>

        <div id="negPromptSection" style="margin-top: 5px; display: none;">
          <label style="font-size: 11px; color: var(--muted); display: block; margin-bottom: 4px;">Negative Prompt / 负向提示词</label>
          <textarea id="pNegPrompt" rows="3"></textarea>
        </div>

        <div id="loraSection" style="margin-top: 5px; font-size: 12px; color: #a5b4fc; display: none;">
          <span style="color: var(--muted); font-size: 11px; display: block; margin-bottom: 4px;">Active LoRA Stack / 挂载的 LoRA 列表:</span>
          <div id="pLoras" style="background: #0b0d13; border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; font-family: monospace;">None</div>
        </div>

        <button id="btnGen" class="btn-generate" onclick="triggerGenerate()">🚀 Render with ComfyUI / 一键调用渲染生成</button>
      </div>

      <div class="card">
        <div class="card-title">📜 Execution Logs / 实时调度日志</div>
        <div class="status-box" id="logBox">[System] Image Agent Studio Ready.</div>
      </div>
    </div>

    <div class="preview-area">
      <div class="card" style="height: 100%; display: flex; flex-direction: column;">
        <div class="card-title">
          <span>🖼️ Generation Preview / 成图预览</span>
          <span id="genInfo" style="font-size: 12px; color: var(--muted);">Waiting / 等待渲染</span>
        </div>
        <div class="preview-container">
          <div id="placeholderText" class="placeholder">
            <svg style="width: 48px; height: 48px; margin-bottom: 12px; opacity: 0.3;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
            <p>Enter instructions or upload a reference image</p>
            <p style="font-size: 11px; margin-top: 4px; color: #64748b;">GPU will render with 100% dedicated VRAM</p>
          </div>
          <img id="resultImage" class="preview-img" style="display: none;" onclick="window.open(this.src)">
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentImageBase64 = null;
    let initialImageLoaded = false;

    function handleImageFile(file, sourceName) {
      if (!file || !file.type.startsWith('image/')) {
        appendLog('⚠️ 忽略非图片文件: ' + (file ? file.type : '未知'));
        return;
      }
      const reader = new FileReader();
      reader.onload = function(evt) {
        currentImageBase64 = evt.target.result;
        
        document.getElementById('dropPrompt').style.display = 'none';
        document.getElementById('dropLoaded').style.display = 'flex';
        document.getElementById('refThumb').src = currentImageBase64;
        document.getElementById('refBadge').style.display = 'inline';
        document.getElementById('refImgName').innerText = sourceName || file.name || '参考图已载入';
        
        const tmpImg = new Image();
        tmpImg.onload = function() {
          document.getElementById('refImgSize').innerText = tmpImg.width + ' × ' + tmpImg.height + ' px';
        };
        tmpImg.src = currentImageBase64;

        appendLog('✅ 已成功加载参考底图：' + (sourceName || file.name) + '，自动进入【图生图/图像编辑】模式');
        fetchStatus();
      };
      reader.readAsDataURL(file);
    }

    document.getElementById('refImage').addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) handleImageFile(file, file.name);
    });

    // 拖拽支持 (Drag and Drop)
    const dropZone = document.getElementById('dropZone');
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('drag-active');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('drag-active');
      }, false);
    });

    dropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        for (let i = 0; i < dt.files.length; i++) {
          if (dt.files[i].type.startsWith('image/')) {
            handleImageFile(dt.files[i], dt.files[i].name);
            break;
          }
        }
      }
    });

    // 全局窗口拖入支持
    window.addEventListener('dragover', (e) => e.preventDefault(), false);
    window.addEventListener('drop', (e) => {
      if (e.target.closest('#dropZone')) return;
      e.preventDefault();
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        for (let i = 0; i < dt.files.length; i++) {
          if (dt.files[i].type.startsWith('image/')) {
            handleImageFile(dt.files[i], '拖拽文件: ' + dt.files[i].name);
            break;
          }
        }
      }
    }, false);

    // 剪贴板粘贴支持 (Paste / Ctrl+V)
    window.addEventListener('paste', function(e) {
      const clipboardData = e.clipboardData || window.clipboardData;
      if (!clipboardData) return;
      const items = clipboardData.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            handleImageFile(file, '剪贴板图片 (' + new Date().toLocaleTimeString() + ')');
            e.preventDefault();
            return;
          }
        }
      }
    });

    function clearImage() {
      currentImageBase64 = null;
      document.getElementById('refImage').value = '';
      document.getElementById('dropPrompt').style.display = 'flex';
      document.getElementById('dropLoaded').style.display = 'none';
      document.getElementById('refBadge').style.display = 'none';
      document.getElementById('refThumb').src = '';
      appendLog('已移除参考底图，将执行【文生图】');
      fetchStatus();
    }

    function appendLog(msg) {
      const b = document.getElementById('logBox');
      const time = new Date().toLocaleTimeString();
      b.innerText += `[${time}] ${msg}\n`;
      b.scrollTop = b.scrollHeight;
    }

    function onWorkflowChange() {
      const wf = document.getElementById('wfSelect').value;
      const pill = document.getElementById('curEnginePill');
      const loraSec = document.getElementById('loraSection');
      const negSec = document.getElementById('negPromptSection');
      const lbl = document.getElementById('lblRatioOrDenoise');

      if (wf === 'qwen') {
        pill.innerText = 'Qwen-Image 2.1 (进阶)';
        pill.className = 'workflow-pill pill-qwen';
        loraSec.style.display = 'none';
        negSec.style.display = 'none';
        lbl.innerText = '画幅比例 (Ratio: 16:9, 2:3, 1:1)';
      } else {
        pill.innerText = 'Anima AIO Yuri (SDXL)';
        pill.className = 'workflow-pill pill-anima';
        loraSec.style.display = 'block';
        negSec.style.display = 'block';
        lbl.innerText = '去噪强度 (Denoise)';
      }
      fetchStatus();
    }

    async function fetchStatus() {
      const wf = document.getElementById('wfSelect').value;
      const hasImg = !!currentImageBase64;
      try {
        const res = await fetch('/api/status?workflow=' + wf + '&has_image=' + (hasImg ? '1' : '0'));
        const data = await res.json();
        document.getElementById('pSteps').value = data.steps || (wf === 'qwen' ? 40 : 28);
        document.getElementById('pCFG').value = data.cfg !== undefined ? data.cfg : (wf === 'qwen' ? 1.0 : 4.0);
        document.getElementById('pRatioOrDenoise').value = data.wh_ratio || data.denoise || (wf === 'qwen' ? '2:3' : 0.50);
        document.getElementById('pSeed').value = data.seed !== undefined ? data.seed : -1;
        document.getElementById('pPrompt').value = data.prompt || '';
        document.getElementById('pNegPrompt').value = data.negative_prompt || '';
        const lorasElem = document.getElementById('pLoras');
        if (lorasElem) {
          lorasElem.innerText = (data.active_loras && data.active_loras.length) ? data.active_loras.join(' | ') : '无';
        }
        
        if (data.latest_image && !initialImageLoaded) {
          initialImageLoaded = true;
          const img = document.getElementById('resultImage');
          const placeholder = document.getElementById('placeholderText');
          img.src = data.latest_image + '?t=' + Date.now();
          img.style.display = 'block';
          placeholder.style.display = 'none';
          appendLog('已加载最近生成的渲染图片。');
        }
        appendLog('已同步读取 [' + (wf === 'qwen' ? 'Qwen-Image 2.1' : 'Anima Yuri') + '] 当前工作流配置。');
      } catch (e) {
        appendLog('读取工作流失败: ' + e);
      }
    }

    function showNotification(title, body) {
      if ('Notification' in window) {
        if (Notification.permission === 'granted') {
          try {
            const notif = new Notification(title, { body: body });
            notif.onclick = function() {
              window.focus();
              notif.close();
            };
          } catch (e) {}
        } else if (Notification.permission !== 'denied') {
          Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
              try {
                const notif = new Notification(title, { body: body });
                notif.onclick = function() {
                  window.focus();
                  notif.close();
                };
              } catch (e) {}
            }
          });
        }
      }
    }

    async function sendToAgent() {
      const instruction = document.getElementById('instruction').value.trim();
      if (!instruction) {
        alert('请输入指令！');
        return;
      }
      const wf = document.getElementById('wfSelect').value;
      const btn = document.getElementById('btnPlan');
      btn.disabled = true;
      btn.innerText = '⏳ 正在调入 Agent 视觉模型规划中...';
      appendLog('正在释放显存，按需调入本地 LLM 大模型 (目标: ' + wf.toUpperCase() + ')...');

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            workflow: wf,
            instruction: instruction,
            image: currentImageBase64
          })
        });
        const ret = await res.json();
        if (ret.status === 'success') {
          appendLog('✅ Agent 规划完成，已即刻卸载释放显存！');
          appendLog('已成功应用新提示词与参数！');
          showNotification('Image Agent Studio', '🧠 Agent 规划完成，已成功应用新提示词与参数！');
          await fetchStatus();
        } else {
          appendLog('❌ Agent 规划错误: ' + (ret.error || '未知错误'));
        }
      } catch (err) {
        appendLog('❌ 请求异常: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerText = '✨ Agent 规划并写入工作流';
      }
    }

    async function triggerGenerate() {
      const wf = document.getElementById('wfSelect').value;
      const btn = document.getElementById('btnGen');
      btn.disabled = true;
      btn.innerText = '⏳ 显卡全力渲染采样中...';
      
      const placeholder = document.getElementById('placeholderText');
      const img = document.getElementById('resultImage');
      const genInfo = document.getElementById('genInfo');
      placeholder.innerHTML = '<div class="spinner"></div><p>ComfyUI 正在推理采样，显卡 100% 显存全力渲染中...</p>';
      img.style.display = 'none';
      appendLog('向 ComfyUI 提交 [' + wf.toUpperCase() + '] API 渲染队列，显存专供出图...');

      const payload = {
        workflow: wf,
        has_image: !!currentImageBase64,
        image: currentImageBase64,
        prompt: document.getElementById('pPrompt').value,
        negative_prompt: document.getElementById('pNegPrompt').value,
        steps: parseInt(document.getElementById('pSteps').value || (wf === 'qwen' ? 40 : 28)),
        cfg: parseFloat(document.getElementById('pCFG').value || (wf === 'qwen' ? 1.0 : 4.0)),
        ratio_or_denoise: document.getElementById('pRatioOrDenoise').value,
        seed: document.getElementById('pSeed').value
      };

      const startTime = Date.now();
      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        const duration = ((Date.now() - startTime) / 1000).toFixed(1);
        if (data.status === 'success' && data.image_url) {
          img.src = data.image_url + '?t=' + Date.now();
          img.style.display = 'block';
          placeholder.style.display = 'none';
          genInfo.innerText = `引擎: ${wf.toUpperCase()} | 耗时: ${duration}s | 种子: ${data.seed || '随机'}`;
          appendLog(`🎉 图像生成成功！渲染耗时: ${duration}秒`);
          showNotification('Image Agent Studio', `🎨 图像渲染完成！生成耗时: ${duration}秒`);
        } else {
          placeholder.innerHTML = '<p style="color: #ef4444;">❌ 生成失败</p><p style="font-size: 12px; margin-top: 4px;">' + (data.error || '未知错误') + '</p>';
          appendLog('❌ 生成失败: ' + (data.error || '未知错误'));
        }
      } catch (err) {
        placeholder.innerHTML = '<p style="color: #ef4444;">❌ 请求异常</p>';
        appendLog('❌ 请求异常: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerText = '🚀 一键调用 ComfyUI 渲染生成';
      }
    }

    window.onload = function() {
      onWorkflowChange();
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
    };
  </script>
</body>
</html>
"""

def get_status_for_workflow(wf="qwen", has_image=None):
    cfg = image_agent_bridge.get_config()
    status = {"prompt": "", "negative_prompt": "", "steps": 40 if wf == "qwen" else 28, "cfg": 1.0 if wf == "qwen" else 4.0, "denoise": 0.55, "wh_ratio": "2:3", "seed": -1, "active_loras": [], "latest_image": None}
    
    if wf == "qwen":
        t2i_path = cfg["qwen_t2i_workflow"]
        i2i_path = cfg["qwen_i2i_workflow"]
        if has_image is True:
            target = i2i_path
        elif has_image is False:
            target = t2i_path
        else:
            t2i_mtime = os.path.getmtime(t2i_path) if os.path.exists(t2i_path) else 0
            i2i_mtime = os.path.getmtime(i2i_path) if os.path.exists(i2i_path) else 0
            target = i2i_path if i2i_mtime > t2i_mtime else t2i_path

        if os.path.exists(target):
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                if "4" in d:
                    status["prompt"] = d["4"].get("inputs", {}).get("prompt", "")
                if "6" in d:
                    inp = d["6"].get("inputs", {})
                    status["steps"] = inp.get("steps", 40)
                    status["cfg"] = inp.get("cfg", 1.0)
                    status["seed"] = inp.get("seed", -1)
                if "5" in d:
                    w = d["5"].get("inputs", {}).get("width", 832)
                    h = d["5"].get("inputs", {}).get("height", 1216)
                    for r, (rw, rh) in image_agent_bridge.WH_RATIO_MAP.items():
                        if rw == w and rh == h:
                            status["wh_ratio"] = r
                            break
            except Exception as e:
                print("[Qwen Status Error]:", e)
    else:
        target = cfg["anima_workflow"]
        if os.path.exists(target):
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if "1610" in data:
                    status["prompt"] = data["1610"].get("inputs", {}).get("value", "")
                if "1611" in data:
                    status["negative_prompt"] = data["1611"].get("inputs", {}).get("value", "")
                if "118" in data:
                    inp = data["118"].get("inputs", {})
                    status["steps"] = inp.get("steps", 28)
                    status["cfg"] = inp.get("cfg", 4.0)
                    status["denoise"] = inp.get("denoise", 0.50)
                    status["seed"] = inp.get("seed", -1)
                for nid in ["1381", "1382", "1383", "1384", "1697"]:
                    if nid in data:
                        for k, v in data[nid].get("inputs", {}).items():
                            if isinstance(v, dict) and v.get("on") and "lora" in v:
                                lora_name = os.path.basename(v["lora"])
                                strength = round(v.get("strength", 1.0), 2)
                                status["active_loras"].append(f"{lora_name} ({strength})")
            except Exception as e:
                print("[Anima Status Error]:", e)

    out_dir = cfg["comfy_output_dir"]
    if os.path.exists(out_dir):
        imgs = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.lower().endswith(('.png', '.jpg', '.webp'))]
        if imgs:
            newest = max(imgs, key=os.path.getmtime)
            status["latest_image"] = f"/api/view_image/{os.path.basename(newest)}"
            
    return status

def save_and_sanitize_image(b64_raw, out_path, max_dim=1280):
    raw_bytes = base64.b64decode(b64_raw)
    try:
        from PIL import Image
        import io
        with Image.open(io.BytesIO(raw_bytes)) as img:
            img = img.convert("RGB")
            w, h = img.size
            if max(w, h) > max_dim:
                scale = max_dim / max(w, h)
                new_w = (int(w * scale) // 8) * 8
                new_h = (int(h * scale) // 8) * 8
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            else:
                new_w = (w // 8) * 8
                new_h = (h // 8) * 8
                if (new_w, new_h) != (w, h):
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img.save(out_path, format="JPEG", quality=95)
            print(f"[Studio] Input image sanitized & resized: {new_w}x{new_h} -> {out_path}")
    except Exception as e:
        print("[Studio] Note: image sanitization fallback:", e)
        with open(out_path, "wb") as f:
            f.write(raw_bytes)

def send_windows_toast(title, message):
    ps1_path = os.path.join(SCRIPT_DIR, "send_toast.ps1")
    if os.path.exists(ps1_path):
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", ps1_path,
            "-Title", title,
            "-Message", message
        ]
        try:
            import subprocess
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
        except Exception as e:
            print("[Toast Error]:", e)

class StudioHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_HEAD(self):
        cfg = image_agent_bridge.get_config()
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith('/api/view_image/'):
            filename = os.path.basename(parsed.path)
            filepath = os.path.join(cfg["comfy_output_dir"], filename)
            if os.path.exists(filepath):
                self.send_response(200)
                ext = os.path.splitext(filename)[1].lower().replace('.', '')
                self.send_header('Content-Type', f'image/{ext}')
                self.send_header('Content-Length', str(os.path.getsize(filepath)))
                self.end_headers()
                return
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        cfg = image_agent_bridge.get_config()
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if parsed.path in ('/', '/index.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        elif parsed.path == '/api/status':
            wf = qs.get("workflow", ["qwen"])[0]
            has_image_param = qs.get("has_image", [None])[0]
            has_image = None
            if has_image_param == "1":
                has_image = True
            elif has_image_param == "0":
                has_image = False
            status = get_status_for_workflow(wf, has_image=has_image)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode('utf-8'))
        elif parsed.path.startswith('/api/view_image/'):
            filename = os.path.basename(parsed.path)
            filepath = os.path.join(cfg["comfy_output_dir"], filename)
            if os.path.exists(filepath):
                self.send_response(200)
                ext = os.path.splitext(filename)[1].lower().replace('.', '')
                self.send_header('Content-Type', f'image/{ext}')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)

    def do_POST(self):
        cfg = image_agent_bridge.get_config()
        comfy_api = cfg["comfy_api_url"]
        input_dir = cfg["comfy_input_dir"]
        output_dir = cfg["comfy_output_dir"]

        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length)

        if parsed.path == '/api/chat':
            try:
                data = json.loads(post_body.decode('utf-8'))
                wf = data.get('workflow', 'qwen')
                instruction = data.get('instruction', '')
                image_b64 = data.get('image')

                temp_img_path = None
                saved_filename = None
                if image_b64 and ',' in image_b64:
                    os.makedirs(input_dir, exist_ok=True)
                    saved_filename = f"agent_ref_{int(time.time())}.jpg"
                    temp_img_path = os.path.join(input_dir, saved_filename)
                    save_and_sanitize_image(image_b64.split(',', 1)[1], temp_img_path)

                print(f"[Studio] Calling LLM Agent for [{wf.upper()}] with instruction: {instruction}")
                try:
                    image_agent_bridge.start_heretic()
                    params = image_agent_bridge.query_heretic(instruction, temp_img_path, workflow=wf)
                    print(f"[Studio] LLM planned: {json.dumps(params, ensure_ascii=False)}")
                    if wf == "qwen":
                        image_agent_bridge.apply_to_qwen_workflow(params, saved_filename)
                    else:
                        image_agent_bridge.apply_to_anima_workflow(params, saved_filename)
                finally:
                    print("[Studio] Releasing LLM from VRAM handover...")
                    image_agent_bridge.kill_heretic()

                send_windows_toast("Image Agent Studio", f"🧠 [{wf.upper()}] Agent 规划完成，工作流参数已就绪！")
                status = get_status_for_workflow(wf, has_image=bool(saved_filename))
                res_data = {"status": "success", "args": status}
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res_data).encode('utf-8'))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode('utf-8'))

        elif parsed.path == '/api/generate':
            try:
                t_start = time.time()
                data = json.loads(post_body.decode('utf-8')) if post_body else {}
                wf = data.get('workflow', 'qwen')
                
                output_node_id = "8"
                cur_seed = random.randint(1, 10**15)
                
                if wf == "qwen":
                    has_image = data.get("has_image", False)
                    image_b64 = data.get("image")
                    t2i_path = cfg["qwen_t2i_workflow"]
                    i2i_path = cfg["qwen_i2i_workflow"]

                    if has_image or (image_b64 and ',' in image_b64):
                        target_workflow = i2i_path
                    elif "has_image" in data and not has_image:
                        target_workflow = t2i_path
                    else:
                        t2i_mtime = os.path.getmtime(t2i_path) if os.path.exists(t2i_path) else 0
                        i2i_mtime = os.path.getmtime(i2i_path) if os.path.exists(i2i_path) else 0
                        target_workflow = i2i_path if i2i_mtime > t2i_mtime else t2i_path

                    with open(target_workflow, 'r', encoding='utf-8') as f:
                        graph = json.load(f)
                    
                    if (has_image or image_b64) and image_b64 and ',' in image_b64:
                        os.makedirs(input_dir, exist_ok=True)
                        saved_filename = f"agent_ref_{int(time.time())}.jpg"
                        temp_img_path = os.path.join(input_dir, saved_filename)
                        save_and_sanitize_image(image_b64.split(',', 1)[1], temp_img_path)
                        if "9" in graph:
                            graph["9"]["inputs"]["image"] = saved_filename

                    if data.get("prompt") and "4" in graph:
                        graph["4"]["inputs"]["prompt"] = data["prompt"]
                    if "6" in graph:
                        ks = graph["6"]["inputs"]
                        if data.get("steps"): ks["steps"] = int(data["steps"])
                        if data.get("cfg"): ks["cfg"] = float(data["cfg"])
                        if data.get("seed") and str(data["seed"]).strip() != "-1":
                            try: cur_seed = int(data["seed"])
                            except ValueError: pass
                        ks["seed"] = cur_seed
                        
                    # Handle resolution from ratio
                    ratio = data.get("ratio_or_denoise", "2:3")
                    if ratio in image_agent_bridge.WH_RATIO_MAP and "5" in graph:
                        w, h = image_agent_bridge.WH_RATIO_MAP[ratio]
                        graph["5"]["inputs"]["width"] = w
                        graph["5"]["inputs"]["height"] = h

                    with open(target_workflow, 'w', encoding='utf-8') as f:
                        json.dump(graph, f, ensure_ascii=False, indent=2)
                    output_node_id = "8"
                else:
                    target_workflow = cfg["anima_workflow"]
                    with open(target_workflow, 'r', encoding='utf-8') as f:
                        graph = json.load(f)

                    # Handle uploaded image for Anima
                    has_image = data.get("has_image", False)
                    image_b64 = data.get("image")
                    saved_filename = None
                    if (has_image or image_b64) and image_b64 and ',' in image_b64:
                        os.makedirs(input_dir, exist_ok=True)
                        saved_filename = f"agent_ref_{int(time.time())}.jpg"
                        temp_img_path = os.path.join(input_dir, saved_filename)
                        save_and_sanitize_image(image_b64.split(',', 1)[1], temp_img_path)
                        if "1608" in graph:
                            graph["1608"]["inputs"]["image"] = saved_filename
                        # Switch to Mode 2 (Img2Img) and disable Mode 4 (Empty Latent)
                        if "1603:1525" in graph:
                            graph["1603:1525"]["inputs"]["boolean"] = True
                        if "1603:1528" in graph:
                            graph["1603:1528"]["inputs"]["boolean"] = False

                    if data.get("prompt") and "1610" in graph:
                        graph["1610"]["inputs"]["value"] = data["prompt"]
                    if data.get("negative_prompt") and "1611" in graph:
                        graph["1611"]["inputs"]["value"] = data["negative_prompt"]
                    if "118" in graph:
                        ks = graph["118"]["inputs"]
                        if data.get("steps"): ks["steps"] = int(data["steps"])
                        if data.get("cfg"): ks["cfg"] = float(data["cfg"])
                        if data.get("ratio_or_denoise"):
                            try: ks["denoise"] = float(data["ratio_or_denoise"])
                            except ValueError: pass
                        
                        # In image-to-image mode, clamp denoise to safe golden range (0.50) if too high
                        if (has_image or saved_filename) and ks.get("denoise", 0.50) > 0.55:
                            print(f"[Studio] Clamping denoise from {ks.get('denoise')} to 0.50 to protect character features & stockings")
                            ks["denoise"] = 0.50

                        if data.get("seed") and str(data["seed"]).strip() != "-1":
                            try: cur_seed = int(data["seed"])
                            except ValueError: pass
                        ks["seed"] = cur_seed

                    # Sync seed to FaceDetailer if present
                    if "1701" in graph:
                        graph["1701"]["inputs"]["seed"] = cur_seed

                    with open(target_workflow, 'w', encoding='utf-8') as f:
                        json.dump(graph, f, ensure_ascii=False, indent=2)
                    output_node_id = "1649"

                # Free leftover VRAM so WanVAE runs on GPU in 0.2s without CPU fallback or timeout
                try:
                    free_req = urllib.request.Request(
                        f"{comfy_api}/free",
                        data=json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    urllib.request.urlopen(free_req, timeout=3)
                except Exception:
                    pass

                # Submit to ComfyUI API (/prompt)
                req = urllib.request.Request(
                    f"{comfy_api}/prompt",
                    data=json.dumps({"prompt": graph}).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                
                res = urllib.request.urlopen(req, timeout=10)
                resp = json.loads(res.read())
                prompt_id = resp.get('prompt_id')
                if not prompt_id:
                    raise RuntimeError("ComfyUI 未返回 prompt_id: " + str(resp))

                print(f"[Generate] Submitted {wf.upper()} prompt to ComfyUI, ID: {prompt_id}, seed: {cur_seed}")

                # Poll ComfyUI history until completion (up to 10 minutes)
                deadline = time.time() + 600
                output_filename = None
                while time.time() < deadline:
                    time.sleep(2)
                    try:
                        hist_req = urllib.request.urlopen(f"{comfy_api}/history/{prompt_id}", timeout=5)
                        hist_data = json.loads(hist_req.read())
                        if prompt_id in hist_data:
                            item = hist_data[prompt_id]
                            status = item.get("status", {})
                            if status.get("status_str") == "error":
                                raise RuntimeError("ComfyUI 执行报错: " + str(status.get("messages")))
                            
                            outputs = item.get("outputs", {})
                            if output_node_id in outputs and outputs[output_node_id].get("images"):
                                output_filename = outputs[output_node_id]["images"][0]["filename"]
                                print(f"[Generate] Image ready from node {output_node_id}: {output_filename}")
                                break
                    except urllib.error.URLError:
                        pass

                # Fallback: find newest image in output dir
                if not output_filename and os.path.exists(output_dir):
                    all_imgs = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.lower().endswith(('.png', '.jpg', '.webp'))]
                    if all_imgs:
                        newest = max(all_imgs, key=os.path.getmtime)
                        if time.time() - os.path.getmtime(newest) < 40:
                            output_filename = os.path.basename(newest)

                if output_filename:
                    # Free ComfyUI VRAM cache after output
                    try:
                        free_req = urllib.request.Request(
                            f"{comfy_api}/free",
                            data=json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8"),
                            headers={"Content-Type": "application/json"}
                        )
                        urllib.request.urlopen(free_req, timeout=3)
                    except Exception:
                        pass

                    elapsed = round(time.time() - t_start, 1)
                    send_windows_toast("Image Agent Studio", f"🎨 [{wf.upper()}] 图像渲染完成！生成耗时约 {elapsed} 秒")
                    rel_url = f"/api/view_image/{output_filename}"
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "image_url": rel_url, "seed": cur_seed}).encode('utf-8'))
                else:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "error": "等待生成超时，未获取到新渲染图片"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode('utf-8'))

def run_server():
    cfg = image_agent_bridge.get_config()
    port = int(cfg.get("studio_port", 7860))
    server = HTTPServer(('127.0.0.1', port), StudioHandler)
    print(f"============================================================")
    print(f" Image Agent Studio GUI Running at http://127.0.0.1:{port}")
    print(f" Supporting: Qwen-Image 2.1 Advanced & Anima AIO Yuri")
    print(f"============================================================")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
