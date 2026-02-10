from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
import json
import asyncio
from pathlib import Path
import tempfile
import shutil
from typing import List
from ultralytics import YOLO
import io

app = FastAPI(title="YOLO Detection API")

# Enable CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YOLO model
model = YOLO('yolov10m.pt')  # Change to yolov10s.pt, yolov10m.pt, etc. as needed

# COCO class names
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 
    'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 
    'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 
    'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 
    'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 
    'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 
    'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 
    'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 
    'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

def get_class_indices(class_names: List[str]) -> List[int]:
    """Convert class names to indices"""
    indices = []
    for name in class_names:
        if name in COCO_CLASSES:
            indices.append(COCO_CLASSES.index(name))
    return indices if indices else None

@app.get("/")
async def root():
    return {"message": "YOLO Detection API", "status": "running"}

@app.post("/detect/image")
async def detect_image(
    file: UploadFile = File(...),
    classes: str = Form(...)
):
    """Detect objects in an image"""
    try:
        # Parse selected classes
        selected_classes = json.loads(classes)
        class_indices = get_class_indices(selected_classes)
        
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Run detection
        results = model(image, classes=class_indices, verbose=False)
        
        # Get annotated image
        annotated_image = results[0].plot()
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Extract detection info
        detections = []
        for box in results[0].boxes:
            detections.append({
                'class': COCO_CLASSES[int(box.cls[0])],
                'confidence': float(box.conf[0]),
                'bbox': box.xyxy[0].tolist()
            })
        
        return JSONResponse({
            'image': f'data:image/jpeg;base64,{img_base64}',
            'detections': detections,
            'count': len(detections)
        })
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post("/detect/video/upload")
async def upload_video(
    file: UploadFile = File(...),
    classes: str = Form(...)
):
    """Upload video and return a video ID for streaming detection"""
    try:
        # Create temp file
        temp_dir = tempfile.mkdtemp()
        video_path = Path(temp_dir) / file.filename
        
        # Save uploaded video
        with open(video_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Store video info (in production, use a database)
        video_id = str(hash(str(video_path)))
        
        return JSONResponse({
            'video_id': video_id,
            'video_path': str(video_path),
            'classes': classes
        })
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.websocket("/ws/detect/video/{video_id}")
async def websocket_video_detect(websocket: WebSocket, video_id: str):
    """Stream live detection results via WebSocket"""
    await websocket.accept()
    
    try:
        # Receive video info
        data = await websocket.receive_json()
        video_path = data['video_path']
        selected_classes = json.loads(data['classes'])
        class_indices = get_class_indices(selected_classes)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Run detection
            results = model(frame, classes=class_indices, verbose=False)
            annotated_frame = results[0].plot()
            
            # Resize for faster transmission (optional)
            height, width = annotated_frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                new_width = 1280
                new_height = int(height * scale)
                annotated_frame = cv2.resize(annotated_frame, (new_width, new_height))
            
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Extract detections
            detections = []
            for box in results[0].boxes:
                detections.append({
                    'class': COCO_CLASSES[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist()
                })
            
            # Send frame and detection data
            await websocket.send_json({
                'frame': f'data:image/jpeg;base64,{frame_base64}',
                'detections': detections,
                'frame_number': frame_count,
                'total_frames': total_frames,
                'progress': (frame_count / total_frames) * 100
            })
            
            # Control frame rate (adjust based on processing speed)
            await asyncio.sleep(0.01)
        
        cap.release()
        
        # Send completion message
        await websocket.send_json({
            'completed': True,
            'total_detections': frame_count
        })
        
    except WebSocketDisconnect:
        print(f"Client disconnected from video {video_id}")
    except Exception as e:
        await websocket.send_json({'error': str(e)})
    finally:
        await websocket.close()

@app.post("/detect/video/process")
async def process_video_complete(
    file: UploadFile = File(...),
    classes: str = Form(...)
):
    """Process entire video and return processed video file"""
    try:
        selected_classes = json.loads(classes)
        class_indices = get_class_indices(selected_classes)
        
        # Save uploaded video
        temp_dir = tempfile.mkdtemp()
        input_path = Path(temp_dir) / file.filename
        output_path = Path(temp_dir) / f"processed_{file.filename}"
        
        with open(input_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Open video
        cap = cv2.VideoCapture(str(input_path))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        all_detections = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run detection
            results = model(frame, classes=class_indices, verbose=False)
            annotated_frame = results[0].plot()
            
            # Write frame
            out.write(annotated_frame)
            
            # Collect detections
            for box in results[0].boxes:
                all_detections.append({
                    'class': COCO_CLASSES[int(box.cls[0])],
                    'confidence': float(box.conf[0])
                })
        
        cap.release()
        out.release()
        
        # Return processed video
        def iterfile():
            with open(output_path, 'rb') as f:
                yield from f
        
        headers = {
            'x-detection-results': json.dumps({
                'total_detections': len(all_detections),
                'detections': all_detections[:100]  # Limit to avoid header size issues
            })
        }
        
        return StreamingResponse(
            iterfile(),
            media_type='video/mp4',
            headers=headers
        )
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)