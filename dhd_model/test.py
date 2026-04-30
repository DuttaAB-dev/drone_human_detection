import argparse
import glob
import os
import shutil

import cv2
import numpy as np
import supervision as sv
import torch

print("CUDA:", torch.cuda.is_available())
print("Device name:", torch.cuda.get_device_name(0))

# Default Testing config
default_model = "yolo"
default_yolo_model_path = "yolov26s_trained_v1_best.pt"
default_rf_detr_model_path = "rf-detr-base.pth"
default_input_video = "video.mp4"


# for yolo
def test_yolo(model_path, input_video):

    from ultralytics import YOLO

    # Define the model path
    # model_path = "yolo26s.pt"
    model = YOLO(model_path)

    # Extract the model name from the model_path
    model_name = (
        os.path.splitext(os.path.basename(model_path))[0]
        if model_path
        else "unknown_model"
    )

    print(f"Starting prediction with model: {model_name}")

    # Run inference with save=True to save the output video
    results = model("video.mp4", stream=True, save=True, device="cuda")

    # The results object is an iterator. We need to iterate through it
    # to ensure the saving process completes when save=True.
    # However, if save=True, the results are typically saved by the YOLO library itself
    # into a directory like 'runs/detect/predictX'.
    # We just need to consume the iterator to trigger the saving.
    for r in results:
        pass  # Process results if needed, otherwise just consume the iterator

    # After prediction, locate the latest 'predict' directory
    runs_dir = "runs/detect"
    predict_dirs = glob.glob(os.path.join(runs_dir, "predict*"))

    if predict_dirs:
        # Sort by modification time to get the latest directory
        latest_predict_dir = max(predict_dirs, key=os.path.getmtime)
        print(f"Output saved in: {latest_predict_dir}")

        # We need to find the actual saved video file within this directory.
        original_output_video_path = os.path.join(
            latest_predict_dir, os.path.basename("video.avi")
        )

        if os.path.exists(original_output_video_path):
            # Create a new filename including the model name
            new_output_video_filename = f"{os.path.splitext(os.path.basename(original_output_video_path))[0]}_{model_name}{os.path.splitext(original_output_video_path)[1]}"
            new_output_video_path = os.path.join(
                os.path.dirname(original_output_video_path), new_output_video_filename
            )

            # Rename the file
            shutil.move(original_output_video_path, new_output_video_path)
            print(f"Renamed output video to: {new_output_video_path}")
        else:
            print(f"Could not find the output video at {original_output_video_path}")
    else:
        print(f"No prediction directories found in {runs_dir}.")


# for rf-detr


def load_rfdetr_model(model_path):
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
        actual_model = (
            getattr(inner, "module", None) or getattr(inner, "model", None) or inner
        )
        param = next(iter(actual_model.parameters()))
        print(f"  Model parameters on device: {param.device}")
    except Exception as e:
        print(f"  Could not verify device: {e}")

    return model


def test_rf_detr(model, video_path, target_path):
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video: {video_path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"\n--- Video Info ---")
    print(f"  Resolution : {orig_w}x{orig_h}")
    print(f"  FPS        : {fps}")
    print(f"  Frames     : {total_frames}")
    print(f"  Output     : {target_path}\n")

    # Use mp4v codec — most reliable cross-platform
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(target_path, fourcc, fps, (orig_w, orig_h))

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
            resized = cv2.resize(frame, (560, 560))
            detections = model.predict(resized, threshold=0.5)
            # model.predict() already returns sv.Detections

            # Scale bounding boxes back to original frame size
            if len(detections) > 0:
                scale_x = orig_w / 560
                scale_y = orig_h / 560
                detections.xyxy[:, [0, 2]] *= scale_x
                detections.xyxy[:, [1, 3]] *= scale_y

            annotated = box_annotator.annotate(
                scene=frame.copy(), detections=detections
            )
            annotated = label_annotator.annotate(scene=annotated, detections=detections)
            out.write(annotated)

            if frame_idx % 30 == 0 or frame_idx == 1:
                pct = (frame_idx / total_frames * 100) if total_frames > 0 else 0
                print(
                    f"  Frame {frame_idx}/{total_frames} ({pct:.1f}%) — detections: {len(detections)}"
                )

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        cap.release()
        out.release()
        print(f"\nDone. Processed {frame_idx} frames.")
        print(f"Output saved to: {target_path}")


def main():
    parser = argparse.ArgumentParser(description="Test a model on a video.")
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=default_model,
        help="Type of model to use(YOLO/RF-DETR).",
    )
    parser.add_argument(
        "-p", "--path", type=str, default=None, help="Path to the model."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=default_input_video,
        help="Path to the input video file.",
    )
    args = parser.parse_args()

    if args.path is None:
        args.path = (
            default_yolo_model_path
            if args.model == "yolo"
            else default_rf_detr_model_path
        )

    print(f"Testing {args.model.upper()} model: {args.path} on video: {args.input}")

    if args.model == "yolo":
        test_yolo(args.path, args.input)
    elif args.model == "rf-detr":
        model_obj = load_rfdetr_model(args.path)
        test_rf_detr(model_obj, args.input)
    else:
        print("Invalid model type. Use 'yolo' or 'rf-detr'.")


if __name__ == "__main__":
    main()
