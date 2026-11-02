
import cv2
import base64
from fastapi.datastructures import UploadFile
import numpy as np
from typing import List, Optional

from ultralytics.engine.results import Results

from core.config import COCO_CLASSES
from services.filters import preprocess_image, FILTERS

def get_class_indices(class_names: List[str]) -> Optional[List[int]]:
    """Convert class names to COCO class indices."""
    indices = [COCO_CLASSES.index(name) for name in class_names if name in COCO_CLASSES]
    return indices or None

def get_filter_indices(filter_names: List[str]) -> Optional[List[int]]:
    """Convert filter names to COCO class indices."""


def encode_frame_to_base64(frame: np.ndarray, quality: int = 85) -> str:
    """Encode a BGR frame to a base64 JPEG data URI."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"


def extract_detections(boxes, include_track_id: bool = False) -> List[dict]:
    """Parse YOLO result boxes into a list of detection dicts."""
    detections = []
    for box in boxes:
        entry = {
            'class': COCO_CLASSES[int(box.cls[0])],
            'confidence': float(box.conf[0]),
            'bbox': box.xyxy[0].tolist(),
        }
        if include_track_id:
            entry['track_id'] = int(box.id[0]) if box.id is not None else None
        detections.append(entry)
    return detections


def resize_if_needed(frame: np.ndarray, max_width: int = 1280) -> np.ndarray:
    """Downscale frame width to max_width while preserving aspect ratio."""
    height, width = frame.shape[:2]
    if width > max_width:
        scale = max_width / width
        frame = cv2.resize(frame, (max_width, int(height * scale)))
    return frame

def image_detect(model, image_file: bytes, classes: List[int]|None, filters: List[str]|None) -> List[Results]:
    nparr = np.frombuffer(image_file, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    image = preprocess_image(image, filters)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    return model(image_rgb, classes=classes, verbose=False, agnostic_nms=True)

def video_detect(model, frame: np.ndarray, classes: List[int]|None, filters: List[str]|None, tracker: str) -> List[Results]:
    frame = preprocess_image(frame, filters)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
   
    return model.track(
       frame_rgb,
       classes=classes,
       persist=True,
       tracker=tracker,
       verbose=False,
       agnostic_nms=True
    )
