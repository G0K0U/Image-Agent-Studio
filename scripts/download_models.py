#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model Manifest & Downloader for Image Agent Studio
Inspects local ComfyUI models directory, identifies missing checkpoints/LoRAs,
and provides direct download links and commands.
"""

import os
import sys
import argparse

MODELS_MANIFEST = {
    "qwen_image_21": {
        "description": "Qwen-Image 2.1 Diffusion Model & Text Encoders",
        "files": [
            {
                "name": "qwen-image-2.1-Q4_K_M.gguf",
                "subfolder": "diffusion_models",
                "size": "~4.3 GB",
                "source": "https://huggingface.co/city96/Qwen-Image-2.1-GGUF",
                "hf_repo": "city96/Qwen-Image-2.1-GGUF",
                "hf_file": "qwen-image-2.1-Q4_K_M.gguf"
            },
            {
                "name": "qwen3vl_8b_int8_convrot.safetensors",
                "subfolder": "text_encoders",
                "size": "~8.9 GB",
                "source": "https://huggingface.co/Comfy-Org/Qwen-Image-2.1-GGUF",
                "hf_repo": "Comfy-Org/Qwen-Image-2.1-GGUF",
                "hf_file": "split_files/text_encoders/qwen3vl_8b_int8_convrot.safetensors"
            },
            {
                "name": "qwen_image_2.1_vae_bf16.safetensors",
                "subfolder": "vae",
                "size": "~644 MB",
                "source": "https://huggingface.co/Comfy-Org/Qwen-Image-2.1-GGUF",
                "hf_repo": "Comfy-Org/Qwen-Image-2.1-GGUF",
                "hf_file": "split_files/vae/qwen_image_2.1_vae_bf16.safetensors"
            }
        ]
    },
    "anima_aio": {
        "description": "Anima AIO Yuri SDXL Base Checkpoint & Encoders",
        "files": [
            {
                "name": "miaomiaoHarem_animaBase.safetensors",
                "subfolder": "diffusion_models/Anima",
                "size": "~5.5 GB",
                "source": "Civitai / HuggingFace: Cirno-9/Anima",
                "hf_repo": "Cirno-9/Anima",
                "hf_file": "Anima-2.9B-preview-v1.safetensors"
            },
            {
                "name": "qwen_3_06b_base.safetensors",
                "subfolder": "text_encoders",
                "size": "~1.1 GB",
                "source": "https://huggingface.co/Comfy-Org/Anima",
                "hf_repo": "Comfy-Org/Anima",
                "hf_file": "qwen_3_06b_base.safetensors"
            },
            {
                "name": "qwen_image_vae.safetensors",
                "subfolder": "vae",
                "size": "~242 MB",
                "source": "https://huggingface.co/Comfy-Org/Anima",
                "hf_repo": "Comfy-Org/Anima",
                "hf_file": "qwen_image_vae.safetensors"
            }
        ]
    },
    "core_loras": {
        "description": "Anima Yuri Core Recommended LoRA Stack",
        "files": [
            {
                "name": "Scenery_enchancer-Anima-P3.safetensors",
                "subfolder": "loras",
                "role": "Scenery & Lighting Enhancer (0.5 weight)",
                "source": "Civitai: Anima Scenery Enhancer P3"
            },
            {
                "name": "bakaE79AAEE882A4.Md2S.safetensors",
                "subfolder": "loras",
                "role": "RealSkin / Texture Detailer (0.45 weight)",
                "source": "Civitai: RealSkin Slider / Anima Texture"
            },
            {
                "name": "Anima-写实光.safetensors",
                "subfolder": "loras",
                "role": "Photorealistic Light / Darklight (0.65~1.0 weight)",
                "source": "Civitai / Liblib: Anima-写实光"
            },
            {
                "name": "anima_context_detailer_base10.safetensors",
                "subfolder": "loras",
                "role": "Context & Anatomy Detailer (0.5 weight)",
                "source": "Civitai: Anima Context Detailer Base10"
            },
            {
                "name": "anima-highres-aesthetic-boost.safetensors",
                "subfolder": "loras",
                "role": "High-Res Aesthetic Boost (0.5 weight)",
                "source": "Civitai: Anima Highres Aesthetic Boost"
            },
            {
                "name": "Anima_colorfix_v1_by_Volnovik.safetensors",
                "subfolder": "loras",
                "role": "Color Balance & Tone Fixer (0.3 weight)",
                "source": "Civitai: Anima Colorfix Volnovik"
            }
        ]
    },
    "prompt_llm": {
        "description": "Local Agent LLM for Prompt Engineering & VRAM Handover",
        "files": [
            {
                "name": "Qwen3.8-27B-Heretic-Ara-iq4_xs-3.0-mtp.gguf",
                "subfolder": "llm_models",
                "size": "~15.2 GB (IQ4_XS)",
                "source": "HuggingFace: Qwen/Qwen2.5-32B-Instruct or Heretic Qwen 3.8 27B GGUF",
                "note": "Compatible with any local OpenAI-compatible server (llama.cpp, Ollama, LM Studio)"
            }
        ]
    }
}

def check_models(base_models_dir):
    print("==================================================")
    print(" 📦 Image Agent Studio: Model Manifest & Verification")
    print(f" Checking base directory: {base_models_dir}")
    print("==================================================")

    for cat_key, cat_data in MODELS_MANIFEST.items():
        print(f"\n📂 [{cat_data['description']}]")
        for f in cat_data["files"]:
            target_path = os.path.join(base_models_dir, f["subfolder"], f["name"])
            exists = os.path.exists(target_path)
            status_icon = "✅" if exists else "❌ [MISSING]"
            print(f"  {status_icon} {f['name']}")
            print(f"     Target: {f['subfolder']}/{f['name']}")
            if not exists:
                if "hf_repo" in f:
                    print(f"     Download via CLI:")
                    print(f"       huggingface-cli download {f['hf_repo']} {f['hf_file']} --local-dir {os.path.join(base_models_dir, f['subfolder'])}")
                if "source" in f:
                    print(f"     Source URL: {f['source']}")
                if "role" in f:
                    print(f"     Function: {f['role']}")

    print("\n💡 Tip for AI Agents:")
    print("  You can use `huggingface-cli` or aria2c to download the missing weights directly into your ComfyUI models directories.")
    print("==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Model Downloader and Validator")
    parser.add_argument("--models-dir", default="./ComfyUI/models", help="Path to ComfyUI models directory")
    args = parser.parse_args()

    check_models(os.path.abspath(args.models_dir))
