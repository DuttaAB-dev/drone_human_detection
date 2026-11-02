from ultralytics import YOLO
from core.config import MODEL_PATH

_model = None

def get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO(MODEL_PATH)
    return _model
