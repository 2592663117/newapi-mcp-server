"""NewAPI MCP Server - 对接 NewAPI 生图模型 (gpt-image-2)
支持 Streamable HTTP 模式，可部署到魔搭/Render
"""

import os
import json
import logging
import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("newapi-mcp")

NEWAPI_BASE_URL = os.getenv("NEWAPI_BASE_URL", "").rstrip("/")
NEWAPI_API_KEY = os.getenv("NEWAPI_API_KEY", "")

mcp = FastMCP("newapi-image")

@mcp.tool()
async def generate_image(prompt: str, size: str = "1024x1024") -> str:
    """调用 NewAPI 的 gpt-image-2 模型生成图片。
    
    Args:
        prompt: 图片描述（英文效果更好）
        size: 图片尺寸，可选 1024x1024 / 1536x1024 / 1024x1536
    
    Returns:
        生成结果：base64 数据或图片 URL
    """
    if not NEWAPI_BASE_URL:
        return "❌ 错误: 未设置 NEWAPI_BASE_URL 环境变量"
    if not NEWAPI_API_KEY:
        return "❌ 错误: 未设置 NEWAPI_API_KEY 环境变量"
    
    headers = {
        "Authorization": f"Bearer {NEWAPI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": size,
        "n": 1,
        "response_format": "url",
    }
    
    logger.info(f"🎨 生成图片: {prompt[:50]}... 尺寸:{size}")
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{NEWAPI_BASE_URL}/v1/images/generations",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            
            if data.get("data") and len(data["data"]) > 0:
                img = data["data"][0]
                if "url" in img:
                    logger.info(f"✅ 图片生成成功! URL: {img['url'][:80]}...")
                    return json.dumps({"success": True, "url": img["url"]}, ensure_ascii=False)
                elif "b64_json" in img:
                    return json.dumps({"success": True, "format": "base64", "size": len(img["b64_json"])})
            return f"⚠️ 返回异常: {json.dumps(data)}"
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        return f"❌ API错误 ({e.response.status_code}): {e.response.text[:200]}"
    except Exception as e:
        logger.error(f"异常: {e}")
        return f"❌ 请求失败: {str(e)}"

@mcp.tool()
async def list_models() -> str:
    """列出 NewAPI 可用模型（验证连接）"""
    if not NEWAPI_BASE_URL or not NEWAPI_API_KEY:
        return "❌ 未配置环境变量"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{NEWAPI_BASE_URL}/v1/models",
                headers={"Authorization": f"Bearer {NEWAPI_API_KEY}"},
            )
            models = resp.json().get("data", [])
            names = [m.get("id", "") for m in models if "image" in m.get("id", "").lower()]
            return json.dumps({"connected": True, "image_models": names}, ensure_ascii=False)
    except Exception as e:
        return f"❌ 连接失败: {str(e)}"

if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))
    logger.info(f"🚀 启动 NewAPI MCP Server (端口: {port})")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
