import json
import asyncio
import shutil
import tempfile
from pathlib import Path

import cv2
from fastapi import APIRouter, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse

from core.model import get_model
from services.detection import video_detect, get_class_indices, encode_frame_to_base64, extract_detections, resize_if_needed
from services.tracker import get_tracker

router = APIRouter(tags=["Video Detection"])


# @router.post("/detect/video/upload")
# async def upload_video(
#     file: UploadFile = File(...),
#     classes: str = Form(...),
#     filters: str = Form(...),
# ):
#     """Save an uploaded video and return its path + ID for WebSocket streaming."""
#     try:
#         temp_dir = tempfile.mkdtemp()
#         assert file.filename is not None
#         video_path = Path(temp_dir) / file.filename

#         with open(video_path, 'wb') as buffer:
#             shutil.copyfileobj(file.file, buffer)

#         return JSONResponse({
#             'video_id': str(hash(str(video_path))),
#             'video_path': str(video_path),
#             'classes': classes,
#         })

#     except Exception as e:
#         return JSONResponse({'error': str(e)}, status_code=500)


# @router.websocket("/ws/detect/video/{video_id}")
# async def websocket_video_detect(websocket: WebSocket, video_id: str):
#     """Stream per-frame detection results over a WebSocket connection."""
#     await websocket.accept()

#     try:
#         data = await websocket.receive_json()
#         video_path = data['video_path']
#         class_indices = get_class_indices(json.loads(data['classes']))
#         tracker_algo = get_tracker()

#         cap = cv2.VideoCapture(video_path)
#         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         frame_count = 0

#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             frame_count += 1
#             results = get_model().track(frame, classes=class_indices, persist=True, tracker=tracker_algo, verbose=False)
#             annotated = resize_if_needed(results[0].plot())

#             await websocket.send_json({
#                 'frame': encode_frame_to_base64(annotated),
#                 'detections': extract_detections(results[0].boxes, include_track_id=True),
#                 'frame_number': frame_count,
#                 'total_frames': total_frames,
#                 'progress': round((frame_count / total_frames) * 100, 2),
#             })

#             await asyncio.sleep(0.01)

#         cap.release()
#         await websocket.send_json({'completed': True, 'total_frames': frame_count})

#     except WebSocketDisconnect:
#         print(f"Client disconnected from video stream: {video_id}")
#     except Exception as e:
#         await websocket.send_json({'error': str(e)})
#     finally:
#         await websocket.close()


@router.post("/detect/video/process")
async def process_video_complete(
    file: UploadFile = File(...),
    classes: str = Form(...),
    filters: str = Form(...)
):
    """Process an entire video with tracking and return the annotated video file."""
    try:
        class_indices = get_class_indices(json.loads(classes))
        selected_filters = json.loads(filters)        
        tracker_algo = get_tracker()

        temp_dir = tempfile.mkdtemp()
        assert file.filename is not None
        input_path = Path(temp_dir) / file.filename
        output_path = Path(temp_dir) / f"processed_{file.filename}"

        with open(input_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        cap = cv2.VideoCapture(str(input_path))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*'mp4v'), # type: ignore[attr-defined]
            fps,
            (width, height)
        )

        all_detections = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
        
            results = video_detect(
                get_model(),
                frame,
                class_indices,
                selected_filters,
                tracker_algo,
            )

            results[0].names = {k: "" for k in results[0].names}
            
            out.write(results[0].plot())
        
            if results[0].boxes is not None:
                all_detections.extend(
                    extract_detections(results[0].boxes, include_track_id=True)
                )
        
        cap.release()
        out.release()

        headers = {
            'x-detection-results': json.dumps({
                'total_detections': len(all_detections),
                'detections': all_detections[:100],  # cap to avoid header size limits
            })
        }

        def stream_file():
            with open(output_path, 'rb') as f:
                yield from f

        return StreamingResponse(stream_file(), media_type='video/mp4', headers=headers)

    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
