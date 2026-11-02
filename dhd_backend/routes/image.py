import json
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse

from core.model import get_model
from services.detection import image_detect, get_class_indices, encode_frame_to_base64, extract_detections

router = APIRouter(prefix="/detect", tags=["Image Detection"])


@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
    classes: str = Form(...),
    filters: str = Form(...)
):
    """Detect objects in a single uploaded image."""
    try:
        selected_classes = json.loads(classes)
        class_indices = get_class_indices(selected_classes)

        selected_filters = json.loads(filters)
        # filter_indices = get_class_indices(selected_filters)
        

        image_file = await file.read()

        results = image_detect(
            get_model(),
            image_file,
            class_indices,
            selected_filters
        )
        results[0].names = {k: "" for k in results[0].names}
        annotated = results[0].plot()

        return JSONResponse({
            'image': encode_frame_to_base64(annotated, quality=95),
            'detections': extract_detections(results[0].boxes),
            'count': len(results[0].boxes) if results[0].boxes is not None else 0,
        })

    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
