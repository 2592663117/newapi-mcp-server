"""NewAPI MCP Server - Streamable HTTP mode for Render deployment."""

import os
import json
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

NEWAPI_BASE_URL = os.getenv("NEWAPI_BASE_URL", "https://jiuuij.de5.net")
NEWAPI_API_KEY = os.getenv("NEWAPI_API_KEY", "")

mcp = FastMCP("newapi-mcp-server")

@mcp.tool()
async def generate_image(prompt: str, size: str = "1024x1024") -> str:
    """Generate image using NewAPI gpt-image-2 model."""
    if not NEWAPI_API_KEY:
        return "Error: NEWAPI_API_KEY not configured"
    
    headers = {
        "Authorization": f"Bearer {NEWAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": size,
        "n": 1,
        "response_format": "b64_json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{NEWAPI_BASE_URL}/v1/images/generations",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            if "data" in data and len(data["data"]) > 0:
                image_data = data["data"][0]
                if "b64_json" in image_data:
                    return f"Image generated successfully (base64, {len(image_data['b64_json'])} chars)"
                elif "url" in image_data:
                    return f"Image URL: {image_data['url']}"
            return f"Response: {json.dumps(data)}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.resource("newapi://status")
def get_status() -> str:
    return json.dumps({"server": "newapi-mcp-server", "version": "0.1.0"}, indent=2)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
