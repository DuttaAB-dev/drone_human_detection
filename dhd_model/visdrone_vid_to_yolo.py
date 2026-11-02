import os
import shutil
from pathlib import Path
from PIL import Image

VISDRONE_CLASSES = {
    1: 0,   # pedestrian
    2: 1,   # people
    3: 2,   # bicycle
    4: 3,   # car
    5: 4,   # van
    6: 5,   # truck
    7: 6,   # tricycle
    8: 7,   # awning-tricycle
    9: 8,   # bus
    10: 9,  # motor
}

def convert_visdrone_vid_to_yolo(dataset_dir, output_label_dir, output_img_dir=None, use_symlinks=True):
    """
    dataset_dir: e.g. 'VisDrone2019-VID-train'
    Expects: dataset_dir/sequences/<seq_name>/*.jpg
             dataset_dir/annotations/<seq_name>.txt
    """
    seq_dir   = Path(dataset_dir) / "sequences"
    anno_dir  = Path(dataset_dir) / "annotations"
    
    label_dir = Path(output_label_dir)
    label_dir.mkdir(parents=True, exist_ok=True)
    
    # If no specific image output directory is passed, put it next to labels
    if output_img_dir is None:
        img_dir = Path(dataset_dir) / "images"
    else:
        img_dir = Path(output_img_dir)
    img_dir.mkdir(parents=True, exist_ok=True)

    skipped = 0
    converted = 0

    print(f"Starting conversion for {dataset_dir}...")

    for anno_file in sorted(anno_dir.glob("*.txt")):
        seq_name = anno_file.stem  # e.g. uav0000013_00000_v

        # Build frame_id -> list of annotations
        frame_annotations = {}
        with open(anno_file) as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) < 8:
                    continue

                frame_id  = int(parts[0])
                x         = int(parts[2])
                y         = int(parts[3])
                w         = int(parts[4])
                h         = int(parts[5])
                category  = int(parts[7])

                if category not in VISDRONE_CLASSES or w <= 0 or h <= 0:
                    continue

                frame_annotations.setdefault(frame_id, []).append((x, y, w, h, category))

        # Process each frame image in the sequence
        img_seq_dir = seq_dir / seq_name
        if not img_seq_dir.exists():
            print(f"[WARN] Sequence folder not found: {img_seq_dir}")
            skipped += 1
            continue

        for img_path in sorted(img_seq_dir.glob("*.jpg")):
            # VID frame files are like 0000001.jpg — frame_id is the number
            frame_id = int(img_path.stem)

            # Load image dimensions for normalization
            with Image.open(img_path) as img:
                img_w, img_h = img.size

            yolo_lines = []
            for (x, y, w, h, category) in frame_annotations.get(frame_id, []):
                yolo_class = VISDRONE_CLASSES[category]
                
                # Normalize and bound to [0, 1]
                x_center = min(max((x + w / 2) / img_w, 0), 1)
                y_center = min(max((y + h / 2) / img_h, 0), 1)
                norm_w   = min(max(w / img_w, 0), 1)
                norm_h   = min(max(h / img_h, 0), 1)
                
                yolo_lines.append(
                    f"{yolo_class} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}"
                )

            # 1. Save label file with unique prefix identifier
            out_lbl_name = f"{seq_name}__{img_path.stem}.txt"
            with open(label_dir / out_lbl_name, "w") as f:
                f.write("\n".join(yolo_lines))

            # 2. Map the image file with the identical unique name prefix
            out_img_name = f"{seq_name}__{img_path.stem}.jpg"
            dst_img_path = img_dir / out_img_name

            if not dst_img_path.exists():
                if use_symlinks:
                    try:
                        # Creates a lightweight reference pointer rather than duplicating disk space
                        dst_img_path.symlink_to(img_path.resolve())
                    except OSError:
                        # Fallback to copy if user lacks system privileges for creating symlinks
                        shutil.copy(img_path, dst_img_path)
                else:
                    shutil.copy(img_path, dst_img_path)

            converted += 1

    print(f"Done. Converted: {converted} frames | Skipped sequences: {skipped}\n")


if __name__ == "__main__":
    # Process Train Directory
    convert_visdrone_vid_to_yolo(
        dataset_dir="datasets/VisDrone2019-VID-train",
        output_label_dir="datasets/VisDroneYOLO2019-VID-train/labels"
    )

    # Process Validation Directory
    convert_visdrone_vid_to_yolo(
        dataset_dir="datasets/VisDrone2019-VID-val",
        output_label_dir="datasets/VisDrone2019-VID-val/labels"
    )