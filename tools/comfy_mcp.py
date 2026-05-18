#!/usr/bin/env python3
"""MCP server for local ComfyUI image generation. Requires ComfyUI running."""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

COMFY_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = Path.home() / ".hermes" / "comfy_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# SDXL default workflow — simple text-to-image
DEFAULT_WORKFLOW = {
    "3": {"class_type": "KSampler", "inputs": {
        "seed": 42, "steps": 20, "cfg": 7.5,
        "sampler_name": "euler", "scheduler": "normal",
        "denoise": 1.0,
        "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
        "latent_image": ["5", 0]
    }},
    "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
    "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "6": {"class_type": "CLIPTextEncode", "inputs": {
        "text": "masterpiece, best quality",
        "clip": ["4", 1]
    }},
    "7": {"class_type": "CLIPTextEncode", "inputs": {
        "text": "low quality, blurry, distorted",
        "clip": ["4", 1]
    }},
    "8": {"class_type": "VAEDecode", "inputs": {
        "samples": ["3", 0], "vae": ["4", 2]
    }},
    "9": {"class_type": "SaveImage", "inputs": {
        "filename_prefix": "hermes_gen",
        "images": ["8", 0]
    }},
}


def check_ready() -> dict:
    """Check if ComfyUI server is running."""
    try:
        req = urllib.request.Request(f"{COMFY_URL}/system_stats", headers={"User-Agent": "Hermes"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            return {"ready": True, "gpu": data.get("system", {}).get("gpu_name", "unknown")}
    except Exception as e:
        return {"ready": False, "error": str(e)}


def generate(prompt: str, negative: str = "", width: int = 1024, height: int = 1024, steps: int = 20) -> dict:
    """Submit a prompt and wait for result."""
    import uuid, time

    # Check ready
    ready = check_ready()
    if not ready["ready"]:
        return {"error": f"ComfyUI not running: {ready.get('error', 'unknown')}"}

    # Build workflow
    wf = json.loads(json.dumps(DEFAULT_WORKFLOW))
    wf["6"]["inputs"]["text"] = f"masterpiece, best quality, {prompt}"
    wf["7"]["inputs"]["text"] = negative or "low quality, blurry, distorted"
    wf["3"]["inputs"]["seed"] = hash(prompt) % 2**32
    wf["3"]["inputs"]["steps"] = steps
    wf["5"]["inputs"]["width"] = width
    wf["5"]["inputs"]["height"] = height
    wf["9"]["inputs"]["filename_prefix"] = f"hermes_{uuid.uuid4().hex[:8]}"

    payload = {"prompt": wf, "client_id": "hermes-mcp"}

    # Queue prompt
    try:
        req = urllib.request.Request(
            f"{COMFY_URL}/prompt",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "Hermes"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
    except Exception as e:
        return {"error": f"Failed to queue: {e}"}

    prompt_id = result.get("prompt_id", "")
    if not prompt_id:
        return {"error": "No prompt_id returned"}

    # Wait for completion (poll up to 120s)
    for _ in range(120):
        time.sleep(2)
        try:
            hist_url = f"{COMFY_URL}/history/{prompt_id}"
            req = urllib.request.Request(hist_url, headers={"User-Agent": "Hermes"})
            with urllib.request.urlopen(req, timeout=5) as r:
                history = json.loads(r.read())
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                for node_id, node_output in outputs.items():
                    images = node_output.get("images", [])
                    if images:
                        img_info = images[0]
                        filename = img_info.get("filename", "unknown")
                        # Image is in ComfyUI output dir
                        comfy_out = Path("C:/Users/Administrator/Documents/comfy/ComfyUI/output")
                        src = comfy_out / filename
                        if src.exists():
                            import shutil
                            dst = OUTPUT_DIR / filename
                            shutil.copy2(src, dst)
                            return {
                                "path": str(dst),
                                "prompt": prompt,
                                "width": width,
                                "height": height,
                                "steps": steps,
                                "seed": wf["3"]["inputs"]["seed"],
                            }
            # Still processing
        except Exception:
            pass

    return {"error": "Timeout after 120s — image may still be generating"}


def list_tools() -> list:
    return [
        {
            "name": "comfy_generate",
            "description": "Generate an image using local ComfyUI (SDXL). Requires ComfyUI running on port 8188.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image description in English"},
                    "negative": {"type": "string", "description": "Negative prompt (what to avoid)"},
                    "width": {"type": "integer", "description": "Width (default 1024)"},
                    "height": {"type": "integer", "description": "Height (default 1024)"},
                    "steps": {"type": "integer", "description": "Sampling steps (default 20)"},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "comfy_status",
            "description": "Check if local ComfyUI is running and ready.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


def handle_request(req: dict) -> dict | None:
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
            "serverInfo": {"name": "comfy-mcp", "version": "1.0.0"},
        }}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": list_tools()}}
    if method == "tools/call":
        args = req.get("params", {}).get("arguments", {})
        name = req.get("params", {}).get("name", "")
        if name == "comfy_status":
            r = check_ready()
            t = f"ComfyUI: {'READY' if r['ready'] else 'NOT RUNNING'} ({r.get('error', r.get('gpu', ''))})"
        elif name == "comfy_generate":
            r = generate(
                prompt=args.get("prompt", ""),
                negative=args.get("negative", ""),
                width=args.get("width", 1024),
                height=args.get("height", 1024),
                steps=args.get("steps", 20),
            )
            t = f"Image: {r.get('path', 'ERROR')}\n{r.get('error', '')}" if "error" in r else f"Generated: {r.get('path', 'unknown')}\nPrompt: {r.get('prompt', '')}\nSize: {r.get('width', '?')}x{r.get('height', '?')}, {r.get('steps', '?')} steps"
        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Unknown tool"}}
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": t}]}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Unknown"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            if resp: sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n"); sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
