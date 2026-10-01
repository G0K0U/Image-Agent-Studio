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
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

import image_agent_bridge

CONFIG = image_agent_bridge.get_config()

HTML_CONTENT = r"""<!DOCTYPE html>
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
    .container { max-width: 1600px; margin: 0 auto; display: grid; grid-template-columns: 560px 1fr; gap: 24px; align-items: start; }
    header { grid-column: 1 / -1; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
    h1 { font-size: 22px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; }
    .badges { display: flex; gap: 8px; }
    .badge { font-size: 12px; background: #6366f122; color: #a5b4fc; border: 1px solid #6366f144; padding: 3px 10px; border-radius: 999px; }
    .badge-vram { background: #10b98122; color: #34d399; border-color: #10b98144; }
    .sidebar { display: flex; flex-direction: column; gap: 0; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 18px; margin-bottom: 16px; }
    .card-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #f8fafc; display: flex; justify-content: space-between; align-items: center; }
    textarea, input, select { width: 100%; background: #0b0d13; border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: 10px; font-size: 13px; margin-bottom: 10px; font-family: inherit; }
    textarea:focus, input:focus, select:focus { outline: none; border-color: var(--primary); }
    button { width: 100%; background: var(--primary); color: #fff; border: none; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
    button:hover { background: var(--primary-hover); }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-generate { background: var(--accent); margin-top: 10px; font-size: 15px; }
    .param-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 10px; }
    .param-item label { font-size: 11px; color: var(--muted); display: block; margin-bottom: 4px; }
    .param-item input, .param-item select { margin-bottom: 0; }
    .status-box { background: #0b0d13; border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; max-height: 220px; overflow-y: auto; color: #cbd5e1; }
    .preview-area { position: sticky; top: 20px; }
    .preview-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 580px; background: #0b0d13; border: 2px dashed var(--border); border-radius: 12px; overflow: hidden; position: relative; padding: 16px; }
    .preview-img { max-width: 100%; max-height: 820px; object-fit: contain; border-radius: 8px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); cursor: pointer; }
    .placeholder { color: var(--muted); text-align: center; }
    .spinner { border: 4px solid #232838; border-top: 4px solid var(--primary); border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 16px; }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    .thumb-preview { width: 56px; height: 56px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border); flex-shrink: 0; }
    .workflow-pill { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 6px; }
    .pill-qwen { background: #0284c722; color: #38bdf8; border: 1px solid #0284c744; }
    .pill-anima { background: #ec489922; color: #f472b6; border: 1px solid #ec489944; }
    .dropzone { border: 2px dashed var(--border); border-radius: 8px; padding: 12px; text-align: center; background: #0b0d13; transition: all 0.2s ease; margin-top: 4px; outline: none; }
    .dropzone:hover { border-color: var(--primary); background: #10131d; }
    .dropzone:focus { border-color: var(--primary); background: #10131d; box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.35); }
    .dropzone.drag-active { border-color: #38bdf8 !important; background: #0284c718 !important; box-shadow: 0 0 16px rgba(56, 189, 248, 0.35); }
    .dropzone-content { display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--muted); font-size: 12px; }
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

        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px; margin-bottom: 4px;">
          <div class="card-title" style="margin: 0;">🤖 Prompt Instruction / 自然语言指令 (提示词增强源)</div>
          <span id="planStatusBadge" style="font-size: 11px; color: #94a3b8;">等待指令增强</span>
        </div>
        <textarea id="instruction" rows="5" style="min-height: 120px; font-size: 13.5px; line-height: 1.5; resize: vertical;" placeholder="输入自然语言指令（例如：掀开中间的布料 露出清晰私处和屁眼 其余保持不变...）" oninput="markInstructionDirty()"></textarea>
        
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <label style="font-size: 11px; color: var(--muted);">Reference Image / 参考底图 (直接按 Ctrl+V 粘贴或拖入):</label>
            <span id="refBadge" style="font-size: 10px; color: #10b981; display: none;">● 图生图模式已激活</span>
          </div>
          
          <div id="dropZone" class="dropzone" tabindex="0">
            <input type="file" id="refImage" accept="image/*" style="display: none;">
            
            <div id="dropPrompt" class="dropzone-content">
              <svg style="width: 26px; height: 26px; opacity: 0.7; margin-bottom: 2px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2 2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              <span><strong>直接按 Ctrl+V 粘贴图片</strong> 或 <strong>直接拖入文件</strong></span>
              <div style="display: flex; gap: 8px; margin-top: 6px;">
                <button type="button" onclick="pasteFromClipboard(event)" style="width: auto; padding: 5px 14px; font-size: 11px; font-weight: 600; background: #3b82f622; color: #60a5fa; border: 1px solid #3b82f644; border-radius: 4px; cursor: pointer;">📋 粘贴剪贴板图片 (Ctrl+V)</button>
                <button type="button" onclick="document.getElementById('refImage').click(); event.stopPropagation();" style="width: auto; padding: 5px 12px; font-size: 11px; background: #1e293b; color: #cbd5e1; border: 1px solid var(--border); border-radius: 4px; cursor: pointer;">📂 选择本地文件</button>
              </div>
              <span style="font-size: 11px; color: #64748b; margin-top: 2px;">支持截图 (Win+Shift+S)、右键复制图片、网页图片或文件</span>
            </div>

            <div id="dropLoaded" class="dropzone-loaded" style="display: none;" onclick="event.stopPropagation();">
              <div style="display: flex; align-items: center; gap: 10px; overflow: hidden;">
                <img id="refThumb" class="thumb-preview" alt="参考底图" style="cursor: pointer;" onclick="window.open(this.src)" title="点击新窗口查看原图">
                <div style="text-align: left; overflow: hidden;">
                  <div id="refImgName" style="font-size: 12px; font-weight: 600; color: #f8fafc; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">参考图已就绪</div>
                  <div id="refImgSize" style="font-size: 10px; color: var(--muted);">正在读取尺寸...</div>
                </div>
              </div>
              <div style="display: flex; gap: 6px; flex-shrink: 0;">
                <button type="button" onclick="pasteFromClipboard(event)" style="width: auto; padding: 5px 10px; font-size: 11px; background: #3b82f622; color: #60a5fa; border: 1px solid #3b82f644;" title="从系统剪贴板粘贴新图片替换当前底图">📋 粘贴替换</button>
                <button type="button" onclick="document.getElementById('refImage').click()" style="width: auto; padding: 5px 10px; font-size: 11px; background: #334155;">更换</button>
                <button type="button" id="btnClearImg" onclick="clearImage()" style="width: auto; padding: 5px 10px; font-size: 11px; background: #ef444422; color: #f87171; border: 1px solid #ef444444;">移除</button>
              </div>
            </div>
          </div>
        </div>

        <button id="btnPlan" onclick="sendToAgent()" style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);">✨ 提示词增强 / Agent 智能规划写入控制板</button>
      </div>

      <div class="card">
        <div class="card-title">
          <span>⚙️ Workflow Parameters / 参数控制板 (已增强工作流参数)</span>
          <div style="display: flex; gap: 6px; align-items: center;">
            <span id="syncNoticeBadge" style="font-size: 11px; color: #10b981; display: none;">● 已与 Agent 同步</span>
            <button style="width: auto; padding: 2px 8px; font-size: 11px; background: transparent; border: 1px solid var(--border);" onclick="fetchStatus()">Refresh / 刷新</button>
          </div>
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
            <label id="lblDenoise">Denoise / 重绘幅度</label>
            <input type="number" id="pDenoise" step="0.01" min="0.05" max="1.0" placeholder="0.55" title="图生图重绘去噪幅度：0.35-0.45微调/表情；0.50-0.55换装/材质；0.60-0.70深色衣物脱衣/新增私处结构">
          </div>
          <div class="param-item">
            <label id="lblWhRatio">Aspect Ratio / 画幅比例</label>
            <input type="text" id="pWhRatio" placeholder="2:3">
          </div>
          <div class="param-item">
            <label>Seed / 随机种子 (-1 = Random)</label>
            <input type="text" id="pSeed">
          </div>
        </div>

        <div style="margin-top: 10px;">
          <label style="font-size: 11px; color: var(--muted); display: block; margin-bottom: 4px;">Positive Prompt / 正向提示词 (已由 Agent 视觉增强扩展)</label>
          <textarea id="pPrompt" rows="8" style="min-height: 190px; font-size: 13.5px; line-height: 1.5; resize: vertical;"></textarea>
        </div>

        <div id="negPromptSection" style="margin-top: 5px;">
          <label id="lblNegPrompt" style="font-size: 11px; color: var(--muted); display: block; margin-bottom: 4px;">Negative Prompt / 负向提示词 (排斥项与防抹平标记)</label>
          <textarea id="pNegPrompt" rows="4" style="min-height: 95px; font-size: 13px; line-height: 1.4; resize: vertical;"></textarea>
        </div>

        <div id="multiLoraSection" style="margin-top: 12px; padding: 12px; background: rgba(99, 102, 241, 0.06); border: 1px solid rgba(99, 102, 241, 0.22); border-radius: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 6px;">
              <span style="font-size: 12px; font-weight: 600; color: #a5b4fc; letter-spacing: 0.3px;">🧬 Multi-LoRA Stack / 多 LoRA 堆叠管理</span>
              <span id="loraCountBadge" class="badge" style="font-size: 10px; padding: 1px 7px;">0 Active</span>
            </div>
            <div style="display: flex; gap: 6px; align-items: center;">
              <button type="button" onclick="loadSweetSpotPreset()" style="width: auto; padding: 5px 10px; font-size: 11px; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 4px; display: flex; align-items: center; gap: 4px; cursor: pointer; white-space: nowrap;" title="一键载入实测验证的黄金甜点参数（LoRA 0.65/0.55、CFG 2.8、er_sde/beta 及专属抗畸变负向提示词）">
                <span>🎯 载入实测甜点推荐</span>
              </button>
              <button type="button" onclick="addLoraRow()" style="width: auto; padding: 5px 10px; font-size: 11px; background: #4f46e5; border-radius: 4px; display: flex; align-items: center; gap: 4px; cursor: pointer; white-space: nowrap;">
                <span>➕ 添加 LoRA</span>
              </button>
            </div>
          </div>
          
          <div id="loraStackList" style="display: flex; flex-direction: column; gap: 8px; max-height: 240px; overflow-y: auto; padding-right: 2px;">
            <!-- Dynamic LoRA rows -->
          </div>
          
          <div id="emptyLoraNotice" style="font-size: 11px; color: #64748b; text-align: center; padding: 10px; border: 1px dashed var(--border); border-radius: 6px; margin-top: 4px;">
            当前未启用任何 LoRA（直连基础底模出图）。<br>可点击右上角 "➕ 添加 LoRA" 手动挂载，或使用 Agent 智能规划自动匹配。
          </div>
        </div>

        <div style="display: flex; gap: 8px; margin-top: 10px;">
          <button id="btnGen" class="btn-generate" onclick="triggerGenerate()" style="flex: 1; margin-top: 0;">🚀 Render with ComfyUI / 一键调用渲染生成</button>
          <button id="btnStop" type="button" onclick="stopGenerate()" style="width: auto; padding: 0 16px; background: #ef444422; color: #f87171; border: 1px solid #ef444444; border-radius: 8px; font-weight: 600; cursor: pointer; display: none;" title="强制中止当前 ComfyUI 生成任务">⏹️ 停止</button>
        </div>
      </div>
    </div>

    <div class="preview-area">
      <div class="card" style="display: flex; flex-direction: column;">
        <div class="card-title">
          <span>🖼️ Generation Preview / 成图预览</span>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span id="genInfo" style="font-size: 12px; color: var(--muted);">Waiting / 等待渲染</span>
            <button id="btnSetAsRef" type="button" style="width: auto; padding: 4px 10px; font-size: 11px; background: #3b82f622; color: #60a5fa; border: 1px solid #3b82f644; border-radius: 4px; display: none; cursor: pointer;" onclick="setPreviewAsReference()" title="将本张生成图直接设为参考底图（开启图生图/继续迭代）">📋 设为底图(图生图)</button>
            <button id="btnOpenNewTab" type="button" style="width: auto; padding: 4px 10px; font-size: 11px; background: #1e293b; border: 1px solid var(--border); border-radius: 4px; display: none; cursor: pointer;" onclick="openPreviewInNewTab()">🔍 新窗口查看</button>
          </div>
        </div>
        <div class="preview-container">
          <div id="placeholderText" class="placeholder">
            <svg style="width: 48px; height: 48px; margin-bottom: 12px; opacity: 0.3;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2 2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
            <p>Enter instructions or upload a reference image</p>
            <p style="font-size: 11px; margin-top: 4px; color: #64748b;">GPU will render with 100% dedicated VRAM</p>
          </div>
          <img id="resultImage" class="preview-img" style="display: none;" onclick="window.open(this.src)">
        </div>
      </div>

      <div class="card" style="margin-top: 14px;">
        <div class="card-title">
          <span>📜 Execution Logs / 实时调度日志</span>
          <button type="button" style="width: auto; padding: 2px 8px; font-size: 11px; background: transparent; border: 1px solid var(--border); border-radius: 4px; cursor: pointer;" onclick="document.getElementById('logBox').innerText = '[System] Log cleared.'">清空</button>
        </div>
        <div class="status-box" id="logBox" style="max-height: 220px; min-height: 120px;">[System] Image Agent Studio Ready.</div>
      </div>
    </div>
  </div>

  <script>
    let currentImageBase64 = null;
    let initialImageLoaded = false;

    function isImageFile(f) {
      if (!f) return false;
      if (f.type && f.type.startsWith('image/')) return true;
      if (f.name && (/\.(jpe?g|png|webp|bmp|gif|tiff?|avif|jfif)$/i).test(f.name)) return true;
      return false;
    }

    function loadBase64Image(dataUri, sourceName) {
      currentImageBase64 = dataUri;
      document.getElementById('dropPrompt').style.display = 'none';
      document.getElementById('dropLoaded').style.display = 'flex';
      document.getElementById('refThumb').src = currentImageBase64;
      document.getElementById('refBadge').style.display = 'inline';
      document.getElementById('refImgName').innerText = sourceName || '参考图已载入';
      
      const tmpImg = new Image();
      tmpImg.onload = function() {
        document.getElementById('refImgSize').innerText = tmpImg.width + ' × ' + tmpImg.height + ' px';
      };
      tmpImg.src = currentImageBase64;

      appendLog('✅ 已成功载入参考底图：' + (sourceName || '剪贴板图片') + '，已自动激活【图生图/图像编辑】模式');
    }

    function handleImageFile(file, sourceName) {
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(evt) {
        loadBase64Image(evt.target.result, sourceName || file.name || '参考底图');
      };
      reader.onerror = function(err) {
        appendLog('❌ 读取图片文件失败: ' + err);
      };
      reader.readAsDataURL(file);
    }

    async function loadImageFromUrl(url, sourceName) {
      try {
        appendLog('正在解析并获取图片数据: ' + (url.length > 50 ? url.substring(0, 50) + '...' : url));
        const res = await fetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const blob = await res.blob();
        handleImageFile(blob, sourceName || '链接图片');
      } catch (err) {
        try {
          const res = await fetch('/api/proxy_image?url=' + encodeURIComponent(url));
          if (!res.ok) throw new Error('Proxy HTTP ' + res.status);
          const blob = await res.blob();
          handleImageFile(blob, sourceName || '网络图片');
        } catch (err2) {
          appendLog('❌ 读取图片 URL 失败: ' + err2.message);
        }
      }
    }

    async function loadLocalImagePath(filePath) {
      try {
        appendLog('正在从本地磁盘路径读取图片: ' + filePath);
        const res = await fetch('/api/load_local_image', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: filePath })
        });
        const ret = await res.json();
        if (ret.status === 'success' && ret.data) {
          loadBase64Image(ret.data, ret.name || filePath.split('\\').pop());
        } else {
          appendLog('❌ 读取本地图片失败: ' + (ret.error || '找不到文件'));
        }
      } catch (err) {
        appendLog('❌ 请求读取本地图片异常: ' + err);
      }
    }

    function setPreviewAsReference() {
      const img = document.getElementById('resultImage');
      if (img && img.src) {
        loadImageFromUrl(img.src, '已生成的渲染成图');
        appendLog('🔄 已将当前成图设为参考底图，可直接在指令区输入修改要求进行图生图/局部迭代！');
      } else {
        alert('当前尚未生成任何成图！');
      }
    }

    async function pasteFromClipboard(evt) {
      if (evt) {
        evt.stopPropagation();
        evt.preventDefault();
      }
      appendLog('🔍 正在尝试从系统剪贴板读取数据...');
      
      // 1. Try modern clipboard.read()
      if (navigator.clipboard && navigator.clipboard.read) {
        try {
          const items = await navigator.clipboard.read();
          for (const item of items) {
            for (const type of item.types) {
              if (type.startsWith('image/')) {
                const blob = await item.getType(type);
                handleImageFile(blob, '剪贴板图片 (' + new Date().toLocaleTimeString() + ')');
                return;
              }
            }
          }
        } catch (err) {
          console.warn('[Clipboard] navigator.clipboard.read failed:', err);
        }
      }

      // 2. Try clipboard.readText()
      if (navigator.clipboard && navigator.clipboard.readText) {
        try {
          const text = (await navigator.clipboard.readText() || '').trim();
          if (text) {
            if (text.startsWith('data:image/')) {
              loadBase64Image(text, '剪贴板 DataURI 图片');
              return;
            }
            if (/^https?:\/\/.*\.(jpe?g|png|webp|bmp|gif|jfif)(\?.*)?$/i.test(text) || text.includes('/view?filename=') || text.includes('/api/view_image/')) {
              loadImageFromUrl(text, '剪贴板图片链接');
              return;
            }
            if (/^[a-zA-Z]:\\.*\.(jpe?g|png|webp|bmp|jfif)$/i.test(text)) {
              loadLocalImagePath(text);
              return;
            }
          }
        } catch (err) {
          console.warn('[Clipboard] navigator.clipboard.readText failed:', err);
        }
      }

      // 3. Prompt user for direct keyboard Ctrl+V
      appendLog('💡 提示：若浏览器安全限制阻止直接读取剪贴板，请直接按键盘 Ctrl+V 快捷键即可粘贴图片！');
      const dropZone = document.getElementById('dropZone');
      if (dropZone) dropZone.focus();
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
          if (isImageFile(dt.files[i]) || (dt.files[i].type && dt.files[i].type.startsWith('image/'))) {
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
          if (isImageFile(dt.files[i]) || (dt.files[i].type && dt.files[i].type.startsWith('image/'))) {
            handleImageFile(dt.files[i], '拖拽文件: ' + dt.files[i].name);
            break;
          }
        }
      }
    }, false);

    // 全局剪贴板粘贴捕获 (Universal Paste / Ctrl+V - Capture Phase)
    async function handleGlobalPaste(e) {
      const cd = e.clipboardData || window.clipboardData;
      if (!cd) return;

      const isInputFocused = e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA');

      // 1. 优先检测 clipboardData.items (截图工具 Win+Shift+S / 浏览器右键复制图片)
      const items = cd.items;
      if (items && items.length > 0) {
        for (let i = 0; i < items.length; i++) {
          const item = items[i];
          if (item.type && item.type.startsWith('image/')) {
            const blob = item.getAsFile();
            if (blob) {
              e.preventDefault();
              e.stopPropagation();
              appendLog('📋 成功捕获剪贴板图片数据 (类型: ' + item.type + ')');
              handleImageFile(blob, '剪贴板图片 (' + new Date().toLocaleTimeString() + ')');
              return;
            }
          }
        }
      }

      // 2. 检测 clipboardData.files (文件资源管理器中按 Ctrl+C 复制的文件)
      if (cd.files && cd.files.length > 0) {
        for (let i = 0; i < cd.files.length; i++) {
          const file = cd.files[i];
          if (isImageFile(file) || (file.type && file.type.startsWith('image/'))) {
            e.preventDefault();
            e.stopPropagation();
            appendLog('📋 成功捕获剪贴板图片文件: ' + (file.name || '未命名'));
            handleImageFile(file, file.name || ('剪贴板图片 (' + new Date().toLocaleTimeString() + ')'));
            return;
          }
        }
      }

      // 3. 检测 kind === 'file' 的项 (部分截图或粘贴流)
      if (items && items.length > 0) {
        for (let i = 0; i < items.length; i++) {
          const item = items[i];
          if (item.kind === 'file') {
            const file = item.getAsFile();
            if (file && (isImageFile(file) || (file.size && file.size > 0))) {
              e.preventDefault();
              e.stopPropagation();
              appendLog('📋 成功捕获剪贴板文件流: ' + (file.name || item.type));
              handleImageFile(file, file.name || '剪贴板文件');
              return;
            }
          }
        }
      }

      // 4. 检测网页富文本复制的 <img> 标签
      const html = cd.getData('text/html');
      if (html) {
        const m = html.match(/<img[^>]+src=["']([^"']+)["']/i);
        if (m && m[1]) {
          const src = m[1];
          e.preventDefault();
          e.stopPropagation();
          appendLog('📋 捕获网页图片内容: ' + (src.length > 50 ? src.substring(0, 50) + '...' : src));
          if (src.startsWith('data:image/')) {
            loadBase64Image(src, '网页剪贴板图片');
            return;
          } else {
            loadImageFromUrl(src, '网页源图片');
            return;
          }
        }
      }

      // 5. 检测文本中的 Data URI、图片链接或本地路径
      const text = (cd.getData('text') || '').trim();
      if (text) {
        if (text.startsWith('data:image/')) {
          e.preventDefault();
          e.stopPropagation();
          appendLog('📋 捕获 Base64 DataURI 图片数据');
          loadBase64Image(text, 'Base64 剪贴板图片');
          return;
        }
        if (/^https?:\/\/.*\.(jpe?g|png|webp|bmp|gif|jfif)(\?.*)?$/i.test(text) || text.includes('/view?filename=') || text.includes('/api/view_image/')) {
          e.preventDefault();
          e.stopPropagation();
          appendLog('📋 捕获图片链接: ' + text);
          loadImageFromUrl(text, '链接图片');
          return;
        }
        if (/^[a-zA-Z]:\\.*\.(jpe?g|png|webp|bmp|jfif)$/i.test(text)) {
          e.preventDefault();
          e.stopPropagation();
          appendLog('📋 捕获本地图片文件路径: ' + text);
          loadLocalImagePath(text);
          return;
        }
      }

      // 若聚焦在输入框/文本域且剪贴板仅为普通文本，放行默认文本粘贴
      if (isInputFocused) {
        return;
      }
    }

    document.addEventListener('paste', handleGlobalPaste, true);
    window.addEventListener('paste', handleGlobalPaste, true);

    function clearImage() {
      currentImageBase64 = null;
      document.getElementById('refImage').value = '';
      document.getElementById('dropPrompt').style.display = 'flex';
      document.getElementById('dropLoaded').style.display = 'none';
      document.getElementById('refBadge').style.display = 'none';
      document.getElementById('refThumb').src = '';
      appendLog('已移除参考底图，将执行【文生图】');
    }

    function appendLog(msg) {
      const b = document.getElementById('logBox');
      const time = new Date().toLocaleTimeString();
      b.innerText += `[${time}] ${msg}\n`;
      b.scrollTop = b.scrollHeight;
    }

    let availableLorasList = [];

    function updateLoraCountBadge() {
      const rows = document.querySelectorAll('.lora-row');
      let activeCount = 0;
      rows.forEach(r => {
        const chk = r.querySelector('.lora-enable-chk');
        if (chk && chk.checked) activeCount++;
      });
      const badge = document.getElementById('loraCountBadge');
      if (badge) badge.innerText = `${activeCount} 启用 / ${rows.length} 挂载`;
      const emptyNotice = document.getElementById('emptyLoraNotice');
      if (emptyNotice) emptyNotice.style.display = rows.length === 0 ? 'block' : 'none';
    }

    function syncLoraSlider(slider) {
      const row = slider.closest('.lora-row');
      if (!row) return;
      const num = row.querySelector('.lora-num');
      const val = parseFloat(slider.value);
      if (num) num.value = val.toFixed(2);
    }

    function syncLoraNum(numInput) {
      const row = numInput.closest('.lora-row');
      if (!row) return;
      let val = parseFloat(numInput.value);
      if (isNaN(val)) val = 0.8;
      val = Math.min(1.0, Math.max(0.0, val));
      numInput.value = val.toFixed(2);
      const slider = row.querySelector('.lora-slider');
      if (slider) slider.value = val;
    }

    function removeLoraRow(btn) {
      const row = btn.closest('.lora-row');
      if (row) row.remove();
      updateLoraCountBadge();
    }

    function isQwenLoraModel(name) {
      if (!name) return false;
      const low = name.toLowerCase();
      const qwenTokens = ['qwen', 'qi2', 'q21', 'alpaca', 'these', 'realstockings', 'nicegirls', 'penis', 'vagina', 'f23gg', 'posestudio', 'vnccs'];
      return qwenTokens.some(token => low.includes(token));
    }

    function createLoraSelectElement(wf, selectedVal) {
      const sel = document.createElement('select');
      sel.className = 'lora-select';
      sel.style.cssText = 'margin-bottom: 0; flex: 1; font-size: 12px; padding: 6px 8px; background: #0b0d13; border: 1px solid var(--border); border-radius: 6px; color: var(--text);';

      const optDefault = document.createElement('option');
      optDefault.value = '';
      optDefault.textContent = '-- 请选择 LoRA 模型 --';
      sel.appendChild(optDefault);

      if (!availableLorasList || !availableLorasList.length) return sel;

      const groupQwen = document.createElement('optgroup');
      const groupAnima = document.createElement('optgroup');

      if (wf === 'qwen') {
        groupQwen.label = '🌟 Qwen 2.1 专用 LoRA (当前引擎适配)';
        groupAnima.label = '🌸 Anima / SDXL 模型 (与 Qwen 引擎不兼容)';
      } else {
        groupAnima.label = '🌸 Anima / SDXL 专用 LoRA (当前引擎适配)';
        groupQwen.label = '🌟 Qwen 2.1 模型 (与 Anima 引擎不兼容)';
      }

      availableLorasList.forEach(lora => {
        const opt = document.createElement('option');
        opt.value = lora;
        opt.textContent = lora;
        if (isQwenLoraModel(lora)) {
          groupQwen.appendChild(opt);
        } else {
          groupAnima.appendChild(opt);
        }
      });

      if (wf === 'qwen') {
        if (groupQwen.children.length > 0) sel.appendChild(groupQwen);
        if (groupAnima.children.length > 0) sel.appendChild(groupAnima);
      } else {
        if (groupAnima.children.length > 0) sel.appendChild(groupAnima);
        if (groupQwen.children.length > 0) sel.appendChild(groupQwen);
      }

      if (selectedVal) {
        let found = false;
        for (let i = 0; i < sel.options.length; i++) {
          if (sel.options[i].value === selectedVal || sel.options[i].value.endsWith(selectedVal)) {
            sel.selectedIndex = i;
            found = true;
            break;
          }
        }
        if (!found) {
          const customOpt = document.createElement('option');
          customOpt.value = selectedVal;
          customOpt.textContent = selectedVal;
          sel.appendChild(customOpt);
          sel.value = selectedVal;
        }
      }

      return sel;
    }

    function loadSweetSpotPreset() {
      const wf = document.getElementById('wfSelect').value;
      if (wf === 'qwen') {
        // 1. Set KSampler steps & CFG to sweet spot 2.8 / 40 steps
        document.getElementById('pSteps').value = 40;
        document.getElementById('pCFG').value = 2.8;

        // 2. Set Negative prompt with anti-distortion terms
        const negBox = document.getElementById('pNegPrompt');
        const sweetNeg = "fused buttocks, giant single balloon buttock, giant oversized genitalia, massive fan wrinkles, exaggerated wrinkled skin, wrinkled buttocks, gaping orifice, inverted anatomy, upside down anatomy, swollen body, realistic hyper-wrinkled skin, ugly, deformed, mutated crotch, extra limbs, underwear covering, bar censor, mosaic censor, lowres";
        if (!negBox.value.trim() || negBox.value.length < 20) {
          negBox.value = sweetNeg;
        } else if (!negBox.value.includes('fused buttocks')) {
          negBox.value += ', ' + sweetNeg;
        }

        const denoiseEl = document.getElementById('pDenoise');
        if (denoiseEl) denoiseEl.value = '0.65';
        const whEl = document.getElementById('pWhRatio');
        if (whEl && !whEl.value) whEl.value = '2:3';

        // 3. Ensure Anatomical LoRA is loaded with verified sweet spot strength
        const rows = document.querySelectorAll('.lora-row');
        let hasNsfw = false;
        rows.forEach(r => {
          const sel = r.querySelector('.lora-select');
          const num = r.querySelector('.lora-num');
          const slider = r.querySelector('.lora-slider');
          const chk = r.querySelector('.lora-enable-chk');
          if (sel && (sel.value.includes('NSFW') || sel.value.includes('Alpaca') || sel.value.includes('These'))) {
            hasNsfw = true;
            const strVal = sel.value.includes('Alpaca') ? '0.55' : '0.65';
            if (num) num.value = strVal;
            if (slider) slider.value = parseFloat(strVal);
            if (chk) chk.checked = true;
          }
        });
        if (!hasNsfw) {
          const pref = availableLorasList.find(x => x.includes('NSFW Qwen Lora')) || 'NSFW Qwen Lora.safetensors';
          addLoraRow(pref, 0.65, true);
        }
        updateLoraCountBadge();

        appendLog('🎯 [Sweet-Spot] 已载入 Qwen 解剖优化黄金甜点配置：NSFW LoRA 0.65 | CFG 2.8 | Denoise 0.65 | er_sde/beta | 40步 | 专属抗畸变负向提示词');
      } else {
        // Anima Semi-realistic sweet spot
        document.getElementById('pSteps').value = 30;
        document.getElementById('pCFG').value = 4.5;
        const denoiseEl = document.getElementById('pDenoise');
        if (denoiseEl) denoiseEl.value = '0.50';
        const rows = document.querySelectorAll('.lora-row');
        let hasSemi = false;
        rows.forEach(r => {
          const sel = r.querySelector('.lora-select');
          if (sel && sel.value.includes('半写实')) hasSemi = true;
        });
        if (!hasSemi) {
          addLoraRow('Anima-半写实动漫.safetensors', 0.70, true);
          addLoraRow('Anima-RealSkin SliderV2.safetensors', 0.50, true);
        }
        updateLoraCountBadge();
        appendLog('🎯 [Sweet-Spot] 已载入 Anima 半写实黄金甜点配置：半写实 0.70 | RealSkin 0.50 | CFG 4.5 | Denoise 0.50');
      }
    }

    function addLoraRow(initialLora = '', initialStrength = undefined, isEnabled = true) {
      const wf = document.getElementById('wfSelect').value;
      const list = document.getElementById('loraStackList');
      if (!list) return;

      const row = document.createElement('div');
      row.className = 'lora-row';
      row.style.cssText = 'background: #10131d; border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; display: flex; flex-direction: column; gap: 6px;';

      const topRow = document.createElement('div');
      topRow.style.cssText = 'display: flex; align-items: center; gap: 8px;';

      const chk = document.createElement('input');
      chk.type = 'checkbox';
      chk.className = 'lora-enable-chk';
      chk.checked = isEnabled;
      chk.title = '勾选以启用该 LoRA / 取消勾选临时跳过';
      chk.style.cssText = 'width: 16px; height: 16px; margin-bottom: 0; cursor: pointer; accent-color: #6366f1;';
      chk.onchange = updateLoraCountBadge;

      const sel = createLoraSelectElement(wf, initialLora);
      if (!initialLora) {
        if (wf === 'qwen') {
          for (let opt of sel.options) {
            if (opt.value.includes('Alpaca') || opt.value.includes('NSFW') || opt.value.includes('These')) {
              sel.value = opt.value;
              break;
            }
          }
        } else {
          for (let opt of sel.options) {
            if (opt.value.includes('半写实') || opt.value.includes('RealSkin')) {
              sel.value = opt.value;
              break;
            }
          }
        }
      }

      // Default sweet spot strength: 0.55 for Qwen anatomical LoRA, 0.80 for generic
      let defaultStrength = 0.80;
      const lowName = (sel.value || initialLora || '').toLowerCase();
      if (wf === 'qwen' && (lowName.includes('alpaca') || lowName.includes('these') || lowName.includes('nsfw'))) {
        defaultStrength = 0.55;
      }
      const actualStrength = initialStrength !== undefined ? initialStrength : defaultStrength;

      const delBtn = document.createElement('button');
      delBtn.type = 'button';
      delBtn.innerHTML = '✕';
      delBtn.title = '从当前堆叠中移除此 LoRA';
      delBtn.style.cssText = 'width: 28px; height: 28px; padding: 0; font-size: 13px; background: #ef444422; color: #f87171; border: 1px solid #ef444444; border-radius: 4px; flex-shrink: 0; cursor: pointer;';
      delBtn.onclick = function() { removeLoraRow(delBtn); };

      topRow.appendChild(chk);
      topRow.appendChild(sel);
      topRow.appendChild(delBtn);

      const bottomRow = document.createElement('div');
      bottomRow.style.cssText = 'display: flex; align-items: center; gap: 8px; padding-left: 24px;';

      const lbl = document.createElement('span');
      lbl.innerText = '权重:';
      lbl.style.cssText = 'font-size: 11px; color: var(--muted); width: 30px;';

      const slider = document.createElement('input');
      slider.type = 'range';
      slider.className = 'lora-slider';
      slider.min = '0';
      slider.max = '1';
      slider.step = '0.05';
      slider.value = actualStrength;
      slider.style.cssText = 'flex: 1; accent-color: #6366f1; cursor: pointer;';
      slider.oninput = function() { syncLoraSlider(slider); };

      const num = document.createElement('input');
      num.type = 'number';
      num.className = 'lora-num';
      num.min = '0';
      num.max = '1';
      num.step = '0.05';
      num.value = parseFloat(slider.value).toFixed(2);
      num.style.cssText = 'width: 52px; padding: 3px 4px; font-size: 11px; text-align: center; margin-bottom: 0; background: #0b0d13; border: 1px solid var(--border); border-radius: 4px; color: var(--text);';
      num.oninput = function() { syncLoraNum(num); };
      sel.onchange = function() {
        const val = (sel.value || '').toLowerCase();
        if (wf === 'qwen') {
          if (val.includes('nsfw qwen lora') || val.includes('f23gg')) {
            slider.value = 0.65;
            num.value = '0.65';
            const cfgInput = document.getElementById('pCFG');
            if (cfgInput && (parseFloat(cfgInput.value) <= 1.0 || parseFloat(cfgInput.value) > 3.2)) {
              cfgInput.value = '2.8';
            }
            const negBox = document.getElementById('pNegPrompt');
            if (negBox && !negBox.value.includes('smooth crotch')) {
              negBox.value = "smooth crotch, featureless crotch, barbie doll crotch, flat crotch, missing genitalia, erased genitalia, blurry crotch, twisted anatomy, sideways genitals, inverted anatomy, upside down genitals, deformed crotch, fused buttocks, extra limbs, underwear covering, bar censor, mosaic censor, lowres";
            }
            appendLog('🎯 [Sweet-Spot] 检测到挂载 f23gg 旗舰 NSFW LoRA，已自动匹配推荐参数：权重 0.65 | CFG 2.8 | 防抹平负向提示词');
          } else if (val.includes('vagina')) {
            slider.value = 0.65;
            num.value = '0.65';
            const cfgInput = document.getElementById('pCFG');
            if (cfgInput && (parseFloat(cfgInput.value) <= 1.0 || parseFloat(cfgInput.value) > 3.2)) {
              cfgInput.value = '2.8';
            }
            const negBox = document.getElementById('pNegPrompt');
            if (negBox && !negBox.value.includes('smooth crotch')) {
              negBox.value = "smooth crotch, featureless crotch, barbie doll crotch, flat crotch, missing genitalia, erased genitalia, blurry crotch, twisted anatomy, sideways genitals, inverted anatomy, upside down genitals, deformed crotch, fused buttocks, extra limbs, underwear covering, bar censor, mosaic censor, lowres";
            }
            appendLog('🎯 [Sweet-Spot] 检测到挂载解剖优化 LoRA，已自动匹配推荐参数：权重 0.65 | CFG 2.8 | 防抹平负向提示词');
          } else if (val.includes('alpaca') || val.includes('these') || val.includes('nsfw')) {
            slider.value = 0.55;
            num.value = '0.55';
            const cfgInput = document.getElementById('pCFG');
            if (cfgInput && (parseFloat(cfgInput.value) <= 1.0 || parseFloat(cfgInput.value) > 3.2)) {
              cfgInput.value = '2.8';
            }
            const negBox = document.getElementById('pNegPrompt');
            if (negBox && !negBox.value.includes('smooth crotch')) {
              negBox.value = "smooth crotch, featureless crotch, barbie doll crotch, flat crotch, missing genitalia, erased genitalia, blurry crotch, twisted anatomy, sideways genitals, inverted anatomy, upside down genitals, deformed crotch, fused buttocks, extra limbs, underwear covering, bar censor, mosaic censor, lowres";
            }
            appendLog('🎯 [Sweet-Spot] 检测到挂载 TheseAlpacas LoRA，已自动匹配推荐参数：权重 0.55 | CFG 2.8');
          } else if (val.includes('realstockings')) {
            slider.value = 0.65;
            num.value = '0.65';
            appendLog('🧦 [LoRA] 检测到挂载真实丝袜质感 LoRA，已设推荐权重 0.65');
          } else if (val.includes('nicegirls')) {
            slider.value = 0.55;
            num.value = '0.55';
            appendLog('✨ [LoRA] 检测到挂载审美画质增强 LoRA，已设推荐权重 0.55');
          } else if (val.includes('posestudio') || val.includes('qi2')) {
            slider.value = 0.60;
            num.value = '0.60';
            appendLog('💃 [LoRA] 检测到挂载姿势构图控制 LoRA，已设推荐权重 0.60');
          } else if (val.includes('penis')) {
            slider.value = 0.70;
            num.value = '0.70';
            appendLog('🔧 [LoRA] 检测到挂载局部结构修正 LoRA，已设推荐权重 0.70');
          }
        }
      };

      bottomRow.appendChild(lbl);
      bottomRow.appendChild(slider);
      bottomRow.appendChild(num);

      row.appendChild(topRow);
      row.appendChild(bottomRow);

      list.appendChild(row);
      updateLoraCountBadge();
    }

    function renderLoraStack(activeLoras, availableLoras) {
      if (availableLoras && availableLoras.length) {
        availableLorasList = availableLoras;
      }
      const list = document.getElementById('loraStackList');
      if (!list) return;
      list.innerHTML = '';

      if (activeLoras && activeLoras.length) {
        activeLoras.forEach(item => {
          let name = '';
          let st = 0.8;
          let enabled = true;
          if (typeof item === 'string') {
            name = item;
          } else if (typeof item === 'object') {
            name = item.name || item.path || '';
            st = item.strength !== undefined ? item.strength : 0.8;
            enabled = item.enabled !== false;
          }
          if (name) {
            addLoraRow(name, st, enabled);
          }
        });
      }
      updateLoraCountBadge();
    }

    function collectActiveLorasFromUI() {
      const rows = document.querySelectorAll('.lora-row');
      const loras = [];
      rows.forEach(r => {
        const chk = r.querySelector('.lora-enable-chk');
        const sel = r.querySelector('.lora-select');
        const num = r.querySelector('.lora-num');
        if (sel && sel.value) {
          loras.push({
            name: sel.value,
            strength: parseFloat(num ? num.value : 0.8),
            enabled: chk ? chk.checked : true
          });
        }
      });
      return loras;
    }

    function onWorkflowChange() {
      const wf = document.getElementById('wfSelect').value;
      const pill = document.getElementById('curEnginePill');
      const negSec = document.getElementById('negPromptSection');
      const negLbl = document.getElementById('lblNegPrompt');
      if (negSec) negSec.style.display = 'block';

      if (wf === 'qwen') {
        if (pill) {
          pill.innerText = 'Qwen-Image 2.1 (进阶)';
          pill.className = 'workflow-pill pill-qwen';
        }
        if (negLbl) negLbl.innerText = 'Negative Prompt / 负向提示词 (当 CFG > 1.0 时生效，用于排除平滑皮肤/残缺解剖)';
      } else {
        if (pill) {
          pill.innerText = 'Anima AIO Yuri (SDXL)';
          pill.className = 'workflow-pill pill-anima';
        }
        if (negLbl) negLbl.innerText = 'Negative Prompt / 负向提示词';
      }
      fetchStatus();
    }

    let lastPlannedText = '';

    function markInstructionDirty() {
      const cur = (document.getElementById('instruction').value || '').trim();
      const badge = document.getElementById('planStatusBadge');
      if (!badge) return;
      if (!cur) {
        badge.innerHTML = '等待输入指令';
        badge.style.color = '#94a3b8';
      } else if (cur !== lastPlannedText) {
        badge.innerHTML = '⚠️ 指令有变动，请点击下方【提示词增强】写入控制板';
        badge.style.color = '#f59e0b';
      } else {
        badge.innerHTML = '✅ 提示词已增强写入控制板';
        badge.style.color = '#10b981';
      }
    }

    function flashHighlight(el) {
      if (!el) return;
      el.style.transition = 'none';
      el.style.boxShadow = '0 0 0 2px #10b981, 0 0 16px rgba(16, 185, 129, 0.4)';
      el.style.borderColor = '#10b981';
      setTimeout(() => {
        el.style.transition = 'box-shadow 1.5s ease, border-color 1.5s ease';
        el.style.boxShadow = '';
        el.style.borderColor = 'var(--border)';
      }, 1500);
    }

    function applyStatusToUI(data) {
      if (!data) return;
      const wf = document.getElementById('wfSelect').value;
      const pPrompt = document.getElementById('pPrompt');
      const pNegPrompt = document.getElementById('pNegPrompt');
      
      if (data.prompt !== undefined) {
        pPrompt.value = data.prompt || '';
        flashHighlight(pPrompt);
      }
      if (data.negative_prompt !== undefined) {
        pNegPrompt.value = data.negative_prompt || '';
        flashHighlight(pNegPrompt);
      }
      if (data.steps !== undefined) document.getElementById('pSteps').value = data.steps;
      if (data.cfg !== undefined) document.getElementById('pCFG').value = data.cfg;
      if (data.wh_ratio !== undefined) {
        const whEl = document.getElementById('pWhRatio');
        if (whEl) whEl.value = data.wh_ratio;
      }
      if (data.denoise !== undefined) {
        const denoiseEl = document.getElementById('pDenoise');
        if (denoiseEl) denoiseEl.value = data.denoise;
      }
      if (data.seed !== undefined) document.getElementById('pSeed').value = data.seed;
      if (data.active_loras) {
        renderLoraStack(data.active_loras, data.available_loras);
      }
    }

    async function fetchStatus() {
      const wf = document.getElementById('wfSelect').value;
      const hasImg = !!currentImageBase64;
      try {
        const res = await fetch('/api/status?workflow=' + wf + '&has_image=' + (hasImg ? '1' : '0') + '&_t=' + Date.now(), {
          headers: { 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' }
        });
        const data = await res.json();
        applyStatusToUI(data);

        if (data.latest_image && !initialImageLoaded) {
          initialImageLoaded = true;
          const img = document.getElementById('resultImage');
          const placeholder = document.getElementById('placeholderText');
          img.src = data.latest_image + '?t=' + Date.now();
          img.style.display = 'block';
          placeholder.style.display = 'none';
          const btnTab = document.getElementById('btnOpenNewTab');
          if (btnTab) btnTab.style.display = 'inline-block';
          const btnSetRef = document.getElementById('btnSetAsRef');
          if (btnSetRef) btnSetRef.style.display = 'inline-block';
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
        alert('请输入自然语言指令！');
        return;
      }
      const wf = document.getElementById('wfSelect').value;
      const btn = document.getElementById('btnPlan');
      btn.disabled = true;
      btn.innerText = '⏳ 正在调入 Agent 视觉模型增强规划中...';
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
          if (ret.args) {
            applyStatusToUI(ret.args);
          } else {
            await fetchStatus();
          }
          lastPlannedText = instruction;
          markInstructionDirty();
          const syncBadge = document.getElementById('syncNoticeBadge');
          if (syncBadge) {
            syncBadge.style.display = 'inline';
            syncBadge.innerText = '● 已同步 Agent 最新规划 (' + new Date().toLocaleTimeString() + ')';
          }
          appendLog('✅ Agent 提示词增强与规划完成，已即刻卸载释放显存！');
          const promptLen = (ret.args && ret.args.prompt) ? ret.args.prompt.length : 0;
          appendLog(`📝 已成功改写控制板正向提示词 (${promptLen} 字符) 与负向提示词！`);
          showNotification('Image Agent Studio', '🧠 Agent 提示词增强完成，已改写控制板！');
        } else {
          appendLog('❌ Agent 规划错误: ' + (ret.error || '未知错误'));
          alert('Agent 规划失败: ' + (ret.error || '未知错误'));
        }
      } catch (err) {
        appendLog('❌ 请求异常: ' + err);
        alert('请求异常: ' + err);
      } finally {
        btn.disabled = false;
        btn.innerText = '✨ 提示词增强 / Agent 智能规划写入控制板';
      }
    }

    async function triggerGenerate() {
      const wf = document.getElementById('wfSelect').value;
      const btn = document.getElementById('btnGen');

      // Check if user has un-planned instruction
      const curInstruction = (document.getElementById('instruction').value || '').trim();
      if (curInstruction && curInstruction !== lastPlannedText) {
        const shouldEnhanceFirst = confirm('💡 检测到【自然语言指令】有新修改，但尚未执行【提示词增强】写入控制板。\n\n点击【确定】：先由 Agent 增强提示词写入控制板后再生成\n点击【取消】：使用控制板当前现有参数直接生成');
        if (shouldEnhanceFirst) {
          await sendToAgent();
        }
      }

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
        denoise: parseFloat((document.getElementById('pDenoise') ? document.getElementById('pDenoise').value : '') || (wf === 'qwen' ? 0.55 : 0.50)),
        wh_ratio: (document.getElementById('pWhRatio') ? document.getElementById('pWhRatio').value : '2:3') || '2:3',
        ratio_or_denoise: (document.getElementById('pWhRatio') ? document.getElementById('pWhRatio').value : '2:3') || '2:3',
        seed: document.getElementById('pSeed').value,
        loras: collectActiveLorasFromUI()
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
          const btnTab = document.getElementById('btnOpenNewTab');
          if (btnTab) btnTab.style.display = 'inline-block';
          const btnSetRef = document.getElementById('btnSetAsRef');
          if (btnSetRef) btnSetRef.style.display = 'inline-block';
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

    function openPreviewInNewTab() {
      const img = document.getElementById('resultImage');
      if (img && img.src) {
        window.open(img.src);
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

def get_available_loras():
    try:
        cfg = image_agent_bridge.get_config()
        comfy_url = cfg.get("comfy_api_url", "http://127.0.0.1:8191")
        req = urllib.request.Request(f"{comfy_url}/models/loras", headers={"User-Agent": "ImageAgentStudio"})
        with urllib.request.urlopen(req, timeout=2) as res:
            if res.status == 200:
                raw_list = json.loads(res.read().decode('utf-8'))
                return sorted(list(set(raw_list)))
    except Exception:
        pass

    found = set()
    cfg = image_agent_bridge.get_config()
    possible_dirs = [
        cfg.get("comfy_loras_dir", ""),
        os.environ.get("COMFYUI_LORAS_DIR", ""),
        os.path.join(SCRIPT_DIR, "models", "loras"),
        os.path.join(SCRIPT_DIR, "ComfyUI", "models", "loras"),
        os.path.join(os.path.dirname(SCRIPT_DIR), "QwenImage21", "models", "loras"),
        os.path.join(os.path.dirname(SCRIPT_DIR), "ComfyUI", "ComfyUI_windows_portable", "ComfyUI", "models", "loras"),
    ]
    for d in possible_dirs:
        if d and os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(('.safetensors', '.ckpt', '.pt')):
                        rel = os.path.relpath(os.path.join(root, f), d).replace('\\', '/')
                        found.add(rel)
                        found.add(f)
    if found:
        return sorted(list(found))

    # Comprehensive fallback catalog of all known supported LoRAs
    return [
        "NSFW Qwen Lora.safetensors",
        "NSFW_Qwen_TheseAlpacas_V2.safetensors",
        "qwen21_vagina_v1.safetensors",
        "RealStockings_QWEN.safetensors",
        "nicegirls_qwen12.safetensors",
        "VNCCS_QI2_PoseStudioV1.1.safetensors",
        "Qwen2.1_Anime_consistency.safetensors",
        "Q21 make the penis small.safetensors",
        "Scenery_enchancer-Anima-P3.safetensors",
        "bakaE79AAEE882A4.Md2S.safetensors",
        "Anima-写实光.safetensors",
        "anima_context_detailer_base10.safetensors",
        "anima-highres-aesthetic-boost.safetensors",
        "Anima_colorfix_v1_by_Volnovik.safetensors"
    ]

def get_status_for_workflow(wf="qwen", has_image=None):
    cfg = image_agent_bridge.get_config()
    status = {
        "prompt": "",
        "negative_prompt": "",
        "steps": 40 if wf == "qwen" else 28,
        "cfg": 1.0 if wf == "qwen" else 4.0,
        "denoise": 0.55,
        "wh_ratio": "2:3",
        "seed": -1,
        "active_loras": [],
        "latest_image": None,
        "available_loras": get_available_loras()
    }
    
    if wf == "qwen":
        t2i_path = cfg["qwen_t2i_workflow"]
        i2i_path = cfg["qwen_i2i_workflow"]
        active_run = os.path.join(SCRIPT_DIR, "workflows", "active_qwen_run.json")
        if os.path.exists(active_run):
            target = active_run
        elif has_image is True:
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
                    status["negative_prompt"] = d["4"].get("inputs", {}).get("negative_prompt", "")
                if "6" in d:
                    inp = d["6"].get("inputs", {})
                    status["steps"] = inp.get("steps", 40)
                    status["cfg"] = inp.get("cfg", 1.0)
                    if "denoise" in inp:
                        status["denoise"] = float(inp.get("denoise", 0.55))
                    status["seed"] = inp.get("seed", -1)
                if "5" in d:
                    w = d["5"].get("inputs", {}).get("width", 832)
                    h = d["5"].get("inputs", {}).get("height", 1216)
                    for r, (rw, rh) in image_agent_bridge.WH_RATIO_MAP.items():
                        if rw == w and rh == h:
                            status["wh_ratio"] = r
                            break
                if "10" in d and "1" in d:
                    model_link = d["10"].get("inputs", {}).get("model", [])
                    if isinstance(model_link, list) and model_link and model_link[0] != "1":
                        cur_id = model_link[0]
                        chain = []
                        visited = set()
                        while cur_id and cur_id in d and d[cur_id].get("class_type") in ("LoraLoaderModelOnly", "LoraLoader") and cur_id not in visited:
                            visited.add(cur_id)
                            chain.append(cur_id)
                            prev = d[cur_id].get("inputs", {}).get("model", [])
                            cur_id = prev[0] if (isinstance(prev, list) and prev) else None
                        chain.reverse()
                        for nid in chain:
                            inp = d[nid].get("inputs", {})
                            lora = os.path.basename(inp.get("lora_name", ""))
                            st = inp.get("strength_model", 0.8)
                            if lora:
                                status["active_loras"].append({
                                    "name": lora,
                                    "strength": round(float(st), 2),
                                    "enabled": True
                                })
            except Exception as e:
                print("[Qwen Status Error]:", e)
    else:
        active_run = os.path.join(SCRIPT_DIR, "workflows", "active_anima_run.json")
        target = active_run if os.path.exists(active_run) else cfg["anima_workflow"]
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
                seen_names = set()
                for nid in ["1381", "1382", "1383", "1384", "1697"]:
                    if nid in data:
                        for k, v in data[nid].get("inputs", {}).items():
                            if isinstance(v, dict) and v.get("on") and "lora" in v:
                                lora_name = os.path.basename(v["lora"])
                                strength = round(float(v.get("strength", 1.0)), 2)
                                if lora_name not in seen_names:
                                    seen_names.add(lora_name)
                                    status["active_loras"].append({
                                        "name": lora_name,
                                        "path": v["lora"],
                                        "strength": strength,
                                        "enabled": True
                                    })
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
        try:
            cfg = image_agent_bridge.get_config()
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if parsed.path in ('/', '/index.html'):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
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
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
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
            elif parsed.path == '/api/proxy_image':
                target_url = qs.get("url", [""])[0]
                if target_url:
                    try:
                        req = urllib.request.Request(target_url, headers={"User-Agent": "ImageAgentStudio"})
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            ct = resp.headers.get("Content-Type", "image/png")
                            data = resp.read()
                            self.send_response(200)
                            self.send_header('Content-Type', ct)
                            self.send_header('Content-Length', str(len(data)))
                            self.end_headers()
                            self.wfile.write(data)
                            return
                    except Exception as e:
                        print("[Proxy Image Error]:", e)
                self.send_response(400)
                self.end_headers()
            else:
                self.send_response(404)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

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
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
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

                    if "4" in graph:
                        if data.get("prompt"):
                            graph["4"]["inputs"]["prompt"] = data["prompt"]
                        if data.get("negative_prompt") is not None:
                            graph["4"]["inputs"]["negative_prompt"] = data.get("negative_prompt", "")

                    if "6" in graph:
                        ks = graph["6"]["inputs"]
                        if data.get("steps"): ks["steps"] = int(data["steps"])
                        if data.get("cfg"): ks["cfg"] = float(data["cfg"])
                        if data.get("denoise") is not None:
                            try: ks["denoise"] = float(data["denoise"])
                            except (ValueError, TypeError): pass
                        elif data.get("ratio_or_denoise") and not any(c in str(data.get("ratio_or_denoise")) for c in [":", "x", "/"]):
                            try: ks["denoise"] = float(data["ratio_or_denoise"])
                            except (ValueError, TypeError): pass
                        if data.get("seed") and str(data["seed"]).strip() != "-1":
                            try: cur_seed = int(data["seed"])
                            except ValueError: pass
                        ks["seed"] = cur_seed
                        if ks.get("cfg", 1.0) > 1.5:
                            ks["sampler_name"] = "er_sde"
                            ks["scheduler"] = "beta"
                        
                    # Handle resolution from ratio
                    ratio = data.get("wh_ratio") or data.get("ratio_or_denoise", "2:3")
                    if ratio in image_agent_bridge.WH_RATIO_MAP and "5" in graph:
                        w, h = image_agent_bridge.WH_RATIO_MAP[ratio]
                        graph["5"]["inputs"]["width"] = w
                        graph["5"]["inputs"]["height"] = h

                    # Handle Multi-LoRA for Qwen
                    loras_input = data.get("loras")
                    if loras_input is None and data.get("lora"):
                        loras_input = [{"name": data["lora"], "strength": data.get("lora_strength", 0.8), "enabled": True}]
                    image_agent_bridge.apply_qwen_loras_to_graph(graph, loras_input or [])

                    active_qwen_run = os.path.join(SCRIPT_DIR, "workflows", "active_qwen_run.json")
                    with open(active_qwen_run, 'w', encoding='utf-8') as f:
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
                        if "1607" in graph:
                            graph["1607"]["inputs"]["image"] = saved_filename
                        # Switch to Mode 2 (Img2Img) and disable Mode 4 (Empty Latent)
                        if "1603:1525" in graph:
                            graph["1603:1525"]["inputs"]["boolean"] = True
                        if "1603:1528" in graph:
                            graph["1603:1528"]["inputs"]["boolean"] = False
                    elif not has_image:
                        if "1607" in graph:
                            graph["1607"]["inputs"]["image"] = "reference.png"
                        if "1608" in graph:
                            graph["1608"]["inputs"]["image"] = "reference.png"
                        if "1603:1525" in graph:
                            graph["1603:1525"]["inputs"]["boolean"] = False
                        if "1603:1528" in graph:
                            graph["1603:1528"]["inputs"]["boolean"] = True

                    prompt_str = data.get("prompt", "")
                    if prompt_str and "1610" in graph:
                        graph["1610"]["inputs"]["value"] = prompt_str

                    neg_prompt_str = data.get("negative_prompt", "")
                    if neg_prompt_str and "1611" in graph:
                        if any(k in prompt_str.lower() for k in ("semi-realistic", "photorealistic", "半写实", "realskin")):
                            neg_prompt_str = image_agent_bridge.clean_negative_prompt_for_realism(neg_prompt_str)
                        graph["1611"]["inputs"]["value"] = neg_prompt_str

                    if "118" in graph:
                        ks = graph["118"]["inputs"]
                        if data.get("steps"): ks["steps"] = int(data["steps"])
                        if data.get("cfg"): ks["cfg"] = float(data["cfg"])
                        if data.get("denoise") is not None:
                            try: ks["denoise"] = float(data["denoise"])
                            except (ValueError, TypeError): pass
                        elif data.get("ratio_or_denoise"):
                            try: ks["denoise"] = float(data["ratio_or_denoise"])
                            except ValueError: pass
                        
                        # In image-to-image mode, clamp denoise to safe golden range (0.50) if too high
                        if (has_image or saved_filename) and ks.get("denoise", 0.50) > 0.52:
                            print(f"[Studio] Clamping denoise from {ks.get('denoise')} to 0.50 to protect character features & stockings")
                            ks["denoise"] = 0.50

                        if data.get("seed") and str(data["seed"]).strip() != "-1":
                            try: cur_seed = int(data["seed"])
                            except ValueError: pass
                        ks["seed"] = cur_seed

                    # Sync seed to FaceDetailer if present
                    if "1701" in graph:
                        graph["1701"]["inputs"]["seed"] = cur_seed

                    # Handle Multi-LoRA stacking for Anima
                    loras_input = data.get("loras")
                    if loras_input is not None:
                        image_agent_bridge.apply_anima_loras_to_graph(graph, loras_input)

                    active_anima_run = os.path.join(SCRIPT_DIR, "workflows", "active_anima_run.json")
                    with open(active_anima_run, 'w', encoding='utf-8') as f:
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
                            
                            # If prompt finished execution:
                            if status.get("completed", False):
                                for onid, out_obj in outputs.items():
                                    if out_obj.get("images"):
                                        output_filename = out_obj["images"][0]["filename"]
                                        print(f"[Generate] Image ready from alternative node {onid}: {output_filename}")
                                        break
                                if output_filename:
                                    break
                                # Execution finished with no outputs produced
                                raise RuntimeError("ComfyUI 执行已结束，但未产生输出图像（请检查输入图像或节点状态）")
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

        elif parsed.path == '/api/load_local_image':
            try:
                data = json.loads(post_body.decode('utf-8')) if post_body else {}
                img_path = data.get('path', '').strip().strip('"').strip("'")
                if os.path.exists(img_path) and os.path.isfile(img_path):
                    ext = os.path.splitext(img_path)[1].lower().replace('.', '')
                    if ext in ('jpg', 'jpeg', 'png', 'webp', 'bmp', 'jfif'):
                        mime = 'jpeg' if ext in ('jpg', 'jpeg') else ext
                        with open(img_path, 'rb') as f:
                            raw = f.read()
                        b64 = base64.b64encode(raw).decode('utf-8')
                        data_uri = f"data:image/{mime};base64,{b64}"
                        res = {"status": "success", "data": data_uri, "name": os.path.basename(img_path)}
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(res).encode('utf-8'))
                        return
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": f"找不到图片文件: {img_path}"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode('utf-8'))

def run_server():
    cfg = image_agent_bridge.get_config()
    port = int(cfg.get("studio_port", 7860))
    server = ThreadingHTTPServer(('127.0.0.1', port), StudioHandler)
    print(f"============================================================")
    print(f" Image Agent Studio GUI Running at http://127.0.0.1:{port}")
    print(f" Supporting: Qwen-Image 2.1 Advanced & Anima AIO Yuri")
    print(f"============================================================")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
