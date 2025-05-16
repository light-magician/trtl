import os
from typing import Literal, Optional, Type

import openai
from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

# Load environment variables
load_dotenv()


class OpenAIImageInput(BaseModel):
    prompt: str = Field(..., description="Text prompt to generate an image.")
    mode: Literal["generate"] = Field(
        "generate", description="Only 'generate' mode is supported."
    )
    size: Literal["1024x1024", "1024x1792", "1792x1024"] = Field(
        "1024x1024",
        description=(
            "Image dimensions. Supported sizes: "
            "'1024x1024' (square), "
            "'1024x1792' (portrait), "
            "'1792x1024' (landscape)."
        ),
    )
    quality: Literal["standard", "hd"] = Field(
        "standard",
        description="Image quality: 'standard' or 'hd'. 'hd' uses more tokens.",
    )


class OpenAIImageTool(BaseTool):
    name: str = "openai_image_tool"
    description: str = (
        "Generate images using OpenAI's DALL·E 3 API. "
        "Supports only 'generate' mode with fixed size options: "
        "'1024x1024', '1024x1792', or '1792x1024'."
    )
    args_schema: Type[BaseModel] = OpenAIImageInput

    _client: openai.OpenAI = PrivateAttr()

    def __init__(self):
        super().__init__()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables.")
        self._client = openai.OpenAI(api_key=api_key)

    def _run(
        self,
        prompt: str,
        mode: str = "generate",
        size: str = "1024x1024",
        quality: str = "standard",
    ) -> str:
        if mode != "generate":
            return f"Unsupported mode: {mode}. Only 'generate' is available."

        try:
            response = self._client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size=size,
                quality=quality,
                response_format="url",
            )
            return response.data[0].url
        except Exception as e:
            return f"Image generation failed: {e}"
