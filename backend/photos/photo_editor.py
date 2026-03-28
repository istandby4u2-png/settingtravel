"""AI-guided photo editing using Gemini Vision analysis + PIL processing."""

import io
import json
import os
import uuid
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

from google import genai
from google.genai import types

_data_dir = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent.parent / "data")))
OUTPUT_DIR = _data_dir / "edited"


async def analyze_photo(image_bytes: bytes) -> dict:
    """Use Gemini Vision to analyze a photo and suggest edit parameters."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_API_KEY가 설정되지 않았습니다."}

    client = genai.Client(api_key=api_key)

    prompt = """이 사진을 블로그에 올리기 좋게 편집하려고 합니다. 다음 항목을 분석해주세요.

반드시 JSON 형식으로만 응답하세요:
{
  "brightness": {
    "current_level": "dark/normal/bright 중 하나",
    "adjustment_factor": 1.0에서의 조정값 (예: 1.2는 20% 밝게, 0.9는 10% 어둡게),
    "description": "밝기 상태 설명"
  },
  "horizon": {
    "is_tilted": true/false,
    "rotation_degrees": 기울기 보정을 위해 회전할 각도 (-5~5 범위, 시계방향이 양수),
    "description": "수평 상태 설명"
  },
  "sky": {
    "has_sky": true/false,
    "sky_region_top_percent": 하늘이 차지하는 상단 비율 (0~100),
    "saturation_boost": 하늘 채도 증가량 (1.0 기준, 예: 1.3은 30% 증가),
    "description": "하늘 상태 설명"
  },
  "overall_suggestion": "전체적인 편집 제안 한 줄 설명"
}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                        types.Part(text=prompt),
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": f"Gemini Vision 분석 실패: {str(e)}"}


def edit_photo(
    image_bytes: bytes,
    analysis: dict,
    apply_brightness: bool = True,
    apply_horizon: bool = True,
    apply_sky: bool = True,
) -> tuple[bytes | None, str | None]:
    """Apply edits to a photo based on Gemini analysis results."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode == "RGBA":
            img = img.convert("RGB")

        original_size = img.size

        # 1. Brightness adjustment
        if apply_brightness:
            brightness_info = analysis.get("brightness", {})
            factor = brightness_info.get("adjustment_factor", 1.0)
            if isinstance(factor, (int, float)) and factor != 1.0:
                factor = max(0.5, min(2.0, factor))
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(factor)

        # 2. Horizon correction (rotation)
        if apply_horizon:
            horizon_info = analysis.get("horizon", {})
            if horizon_info.get("is_tilted", False):
                degrees = horizon_info.get("rotation_degrees", 0)
                if isinstance(degrees, (int, float)) and abs(degrees) > 0.1:
                    degrees = max(-10, min(10, degrees))
                    img = img.rotate(
                        -degrees,  # PIL rotates counter-clockwise, so negate
                        resample=Image.BICUBIC,
                        expand=False,
                        fillcolor=(0, 0, 0),
                    )
                    # Crop the black borders from rotation
                    img = _crop_rotation_borders(img, degrees)

        # 3. Sky enhancement
        if apply_sky:
            sky_info = analysis.get("sky", {})
            if sky_info.get("has_sky", False):
                sky_pct = sky_info.get("sky_region_top_percent", 0)
                saturation_boost = sky_info.get("saturation_boost", 1.0)
                if (
                    isinstance(sky_pct, (int, float))
                    and sky_pct > 5
                    and isinstance(saturation_boost, (int, float))
                    and saturation_boost > 1.0
                ):
                    img = _enhance_sky(img, sky_pct, saturation_boost)

        # Slight sharpening for blog-quality
        img = img.filter(ImageFilter.SHARPEN)

        # Resize if too large (max 2048px on longest side for blog use)
        max_dim = 2048
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90, optimize=True)
        return buf.getvalue(), None

    except Exception as e:
        return None, f"사진 편집 실패: {str(e)}"


def save_edited_photo(edited_bytes: bytes, prefix: str = "edited") -> str:
    """Save edited photo to disk, return filename."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = OUTPUT_DIR / filename
    filepath.write_bytes(edited_bytes)
    return filename


def _crop_rotation_borders(img: Image.Image, degrees: float) -> Image.Image:
    """Crop black borders introduced by rotation."""
    import math
    w, h = img.size
    angle_rad = abs(math.radians(degrees))

    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    new_w = int(w * cos_a - h * sin_a) if cos_a > sin_a else w
    new_h = int(h * cos_a - w * sin_a) if cos_a > sin_a else h

    new_w = max(int(w * 0.9), min(new_w, w))
    new_h = max(int(h * 0.9), min(new_h, h))

    left = (w - new_w) // 2
    top = (h - new_h) // 2
    return img.crop((left, top, left + new_w, top + new_h))


def _enhance_sky(img: Image.Image, sky_percent: float, boost: float) -> Image.Image:
    """Selectively enhance sky blue saturation in the top portion of the image."""
    arr = np.array(img)
    h, w, _ = arr.shape

    sky_h = int(h * (sky_percent / 100.0))
    if sky_h < 10:
        return img

    sky_region = arr[:sky_h].copy()

    # Convert to float for processing
    sky_float = sky_region.astype(np.float32)

    # Detect blue-ish pixels in the sky region (R < G, B > R, B > 100)
    r, g, b = sky_float[:, :, 0], sky_float[:, :, 1], sky_float[:, :, 2]
    sky_mask = (b > r) & (b > 80) & (g < b + 80)

    # Boost blue channel and slightly reduce red in sky areas
    boost = min(boost, 1.8)

    sky_float[:, :, 2] = np.where(sky_mask, np.minimum(b * boost, 255), b)
    sky_float[:, :, 0] = np.where(sky_mask, np.maximum(r * 0.9, 0), r)

    # Smooth transition at the boundary (gradient feather over 10% of sky height)
    feather_h = max(int(sky_h * 0.15), 5)
    for y in range(sky_h - feather_h, sky_h):
        blend = 1.0 - ((y - (sky_h - feather_h)) / feather_h)
        for c in range(3):
            sky_float[y, :, c] = sky_float[y, :, c] * blend + arr[y, :, c].astype(np.float32) * (1 - blend)

    arr[:sky_h] = sky_float.clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr)
