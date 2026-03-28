import base64
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from photos.google_photos import search_photos, get_photo_bytes, extract_locations_from_text
from photos.photo_editor import analyze_photo, edit_photo, save_edited_photo

router = APIRouter()

EDITED_DIR = Path(__file__).parent.parent / "data" / "edited"


class SearchRequest(BaseModel):
    query: str = ""
    page_size: int = 20
    page_token: str | None = None


class EditRequest(BaseModel):
    photo_id: str
    brightness: bool = True
    horizon: bool = True
    sky: bool = True


class ExtractLocationsRequest(BaseModel):
    text: str


@router.post("/search")
async def search(req: SearchRequest):
    result = await search_photos(
        query=req.query,
        page_size=req.page_size,
        page_token=req.page_token,
    )
    return result


@router.post("/edit")
async def edit(req: EditRequest):
    print(f"[photos] Downloading photo {req.photo_id}...", flush=True)
    img_bytes, err = await get_photo_bytes(req.photo_id)
    if err:
        return {"error": err}

    # Save original for comparison
    original_filename = save_edited_photo(img_bytes, prefix="original")

    print(f"[photos] Analyzing photo with Gemini Vision...", flush=True)
    analysis = await analyze_photo(img_bytes)
    if "error" in analysis:
        return analysis

    print(f"[photos] Applying edits...", flush=True)
    edited_bytes, edit_err = edit_photo(
        img_bytes,
        analysis,
        apply_brightness=req.brightness,
        apply_horizon=req.horizon,
        apply_sky=req.sky,
    )
    if edit_err:
        return {"error": edit_err}

    edited_filename = save_edited_photo(edited_bytes, prefix="edited")

    return {
        "original_filename": original_filename,
        "edited_filename": edited_filename,
        "original_url": f"/api/photos/image/{original_filename}",
        "edited_url": f"/api/photos/image/{edited_filename}",
        "analysis": {
            "brightness": analysis.get("brightness", {}),
            "horizon": analysis.get("horizon", {}),
            "sky": analysis.get("sky", {}),
            "overall_suggestion": analysis.get("overall_suggestion", ""),
        },
    }


@router.get("/image/{filename}")
async def serve_image(filename: str):
    filepath = EDITED_DIR / filename
    if not filepath.exists():
        return {"error": "파일을 찾을 수 없습니다."}
    return FileResponse(filepath, media_type="image/jpeg")


@router.get("/download/{filename}")
async def download_image(filename: str):
    filepath = EDITED_DIR / filename
    if not filepath.exists():
        return {"error": "파일을 찾을 수 없습니다."}
    return FileResponse(
        filepath,
        media_type="image/jpeg",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/extract-locations")
async def extract_locations(req: ExtractLocationsRequest):
    locations = await extract_locations_from_text(req.text)
    return {"locations": locations}
