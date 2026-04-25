import glob
import os
import shutil
import argparse
import numpy as np

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
        os.path.splitext(os.path.basename(model_path))[0] if model_path else "unknown_model"
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


#for RF-DETR
# def load_rfdetr_model(model_path):
#     from rfdetr import RFDETRBase
#     return RFDETRBase(pretrain_weights=model_path)
    
# def test_rf_detr(model, video_path):
#     import supervision as sv
    
#     # model = RFDETRBase(pretrain_weights=model_path)
#     # video_path = ""
#     box_annotator = sv.BoxAnnotator()
#     label_annotator = sv.LabelAnnotator()
#     target_path = "/var/home/anirban/MyProjects/drone_human_detection/dhd_model/runs/detect/rfdetr_detects/video_output.mp4"
#     def callback(frame):
#         # import cv2
#         # frame = cv2.resize(frame, (640, 640))
#         # # Run inference
#         # results = model.predict(frame, threshold=0.5)
        
#         # # Annotate the frame
#         # annotator = sv.BoxAnnotator()
#         # label_annotator = sv.LabelAnnotator()
        
#         # annotated_frame = annotator.annotate(scene=frame.copy(), detections=results)
#         # annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=results)
        
#         # return annotated_frame
        
#         results = model.predict(frame, threshold=0.5)
            
#         # Supervision expects sv.Detections object
#         # If RF-DETR returns raw results, wrap them:
#         detections = sv.Detections.from_rfdetr(results) 
            
#         annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
#         return label_annotator.annotate(scene=annotated_frame, detections=detections)
#     # 4. Process the video
#     try:
#             sv.process_video(
#                 source_path=video_path,
#                 target_path=target_path,
#                 callback=callback
#             )
#     except Exception as e:
#             print(f"An error occurred: {e}")
# 
def load_rfdetr_model(model_path):
    from rfdetr import RFDETRBase
    # Explicitly pass device so it uses your GPU
    return RFDETRBase(pretrain_weights=model_path, device="cuda")

def test_rf_detr(model, video_path):
    import supervision as sv
    import cv2

    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    target_path = "/var/home/anirban/MyProjects/drone_human_detection/dhd_model/runs/detect/rfdetr_detects/video_output.mp4"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    def callback(frame: np.ndarray) -> np.ndarray:
        # RF-DETR Base requires 560x560 input
        resized = cv2.resize(frame, (560, 560))
        
        results = model.predict(resized, threshold=0.5)

        # Handle both older and newer supervision API
        try:
            detections = sv.Detections.from_rfdetr(results)
        except AttributeError:
            # Fallback: build Detections manually from RF-DETR output
            detections = sv.Detections(
                xyxy=results.xyxy,
                confidence=results.confidence,
                class_id=results.class_id,
            )

        annotated = box_annotator.annotate(scene=frame.copy(), detections=detections)
        return label_annotator.annotate(scene=annotated, detections=detections)

    print(f"Processing video: {video_path}")
    print(f"Output will be saved to: {target_path}")
    try:
        sv.process_video(
            source_path=video_path,
            target_path=target_path,
            callback=callback
        )
        print("Video processing complete.")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise  # Re-raise so you see the full traceback

def main():
    parser = argparse.ArgumentParser(description="Test a model on a video.")
    parser.add_argument("-m", "--model", type=str, default=default_model, help="Type of model to use(YOLO/RF-DETR).")
    parser.add_argument("-p", "--path", type=str, default= None, help="Path to the model.")
    parser.add_argument("-i", "--input", type=str, default=default_input_video, help="Path to the input video file.")
    args = parser.parse_args()
    
    if args.path is None:
        args.path = default_yolo_model_path if args.model == "yolo" else default_rf_detr_model_path
        
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