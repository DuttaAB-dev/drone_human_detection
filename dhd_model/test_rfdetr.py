import os
import cv2
import numpy as np
import torch
import supervision as sv

MODEL_PATH = "rf-detr-base.pth"
VIDEO_PATH = "video.mp4"
TARGET_PATH = "runs/detect/rfdetr_detects/video_output.mp4"


def load_model(model_path):
    from rfdetr import RFDETRBase

    print(f"Loading model from: {model_path}")
    # Try passing device directly — supported in newer rfdetr builds
    try:
        model = RFDETRBase(pretrain_weights=model_path, device="cuda")
        print("  Loaded with device='cuda'")
    except TypeError:
        model = RFDETRBase(pretrain_weights=model_path)
        print("  device= param not supported, loaded without it")

    print(f"  Model type: {type(model)}")

    # optimize_for_inference() is recommended by rfdetr itself (warning above)
    # and typically moves the model to GPU + sets eval mode + applies optimisations
    print("  Calling model.optimize_for_inference()...")
    try:
        model.optimize_for_inference()
        print("  optimize_for_inference() OK")
    except Exception as e:
        print(f"  optimize_for_inference() failed: {e} — continuing anyway")

    # Try to verify GPU usage by inspecting internal model parameters
    try:
        inner = model.model  # ModelContext wrapper
        # ModelContext may expose .module or .model
        actual_model = getattr(inner, "module", None) or getattr(inner, "model", None) or inner
        param = next(iter(actual_model.parameters()))
        print(f"  Model parameters on device: {param.device}")
    except Exception as e:
        print(f"  Could not verify device: {e}")

    return model


def process_video(model, video_path, target_path):
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    box_annotator   = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video: {video_path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS)
    orig_w       = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"\n--- Video Info ---")
    print(f"  Resolution : {orig_w}x{orig_h}")
    print(f"  FPS        : {fps}")
    print(f"  Frames     : {total_frames}")
    print(f"  Output     : {target_path}\n")

    # Use mp4v codec — most reliable cross-platform
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out    = cv2.VideoWriter(target_path, fourcc, fps, (orig_w, orig_h))

    if not out.isOpened():
        print("ERROR: VideoWriter failed to open — check output path and codec")
        cap.release()
        return

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1

            # RF-DETR expects 560x560
            resized    = cv2.resize(frame, (560, 560))
            detections = model.predict(resized, threshold=0.5)
            # model.predict() already returns sv.Detections

            # Scale bounding boxes back to original frame size
            if len(detections) > 0:
                scale_x = orig_w / 560
                scale_y = orig_h / 560
                detections.xyxy[:, [0, 2]] *= scale_x
                detections.xyxy[:, [1, 3]] *= scale_y

            annotated = box_annotator.annotate(scene=frame.copy(), detections=detections)
            annotated = label_annotator.annotate(scene=annotated,  detections=detections)
            out.write(annotated)

            if frame_idx % 30 == 0 or frame_idx == 1:
                pct = (frame_idx / total_frames * 100) if total_frames > 0 else 0
                print(f"  Frame {frame_idx}/{total_frames} ({pct:.1f}%) — detections: {len(detections)}")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        cap.release()
        out.release()
        print(f"\nDone. Processed {frame_idx} frames.")
        print(f"Output saved to: {target_path}")


if __name__ == "__main__":
    print(f"CUDA available : {torch.cuda.is_available()}")
    print(f"Device name    : {torch.cuda.get_device_name(0)}\n")

    model = load_model(MODEL_PATH)
    process_video(model, VIDEO_PATH, TARGET_PATH)