import os
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

def convert_visdrone_vid_to_yolo(dataset_dir, output_label_dir):
    """
    dataset_dir: e.g. 'VisDrone2019-VID-train'
    Expects: dataset_dir/sequences/<seq_name>/*.jpg
             dataset_dir/annotations/<seq_name>.txt
    """
    seq_dir   = Path(dataset_dir) / "sequences"
    anno_dir  = Path(dataset_dir) / "annotations"
    label_dir = Path(output_label_dir)
    label_dir.mkdir(parents=True, exist_ok=True)

    skipped = 0
    converted = 0

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

            img = Image.open(img_path)
            img_w, img_h = img.size

            yolo_lines = []
            for (x, y, w, h, category) in frame_annotations.get(frame_id, []):
                yolo_class = VISDRONE_CLASSES[category]
                x_center = min(max((x + w / 2) / img_w, 0), 1)
                y_center = min(max((y + h / 2) / img_h, 0), 1)
                norm_w   = min(max(w / img_w, 0), 1)
                norm_h   = min(max(h / img_h, 0), 1)
                yolo_lines.append(
                    f"{yolo_class} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}"
                )

            # Save label as <seq_name>__<frame_id>.txt to keep names unique
            out_name = f"{seq_name}__{img_path.stem}.txt"
            with open(label_dir / out_name, "w") as f:
                f.write("\n".join(yolo_lines))

            converted += 1

    print(f"Done. Converted: {converted} frames | Skipped sequences: {skipped}")


# Run for train and val
convert_visdrone_vid_to_yolo(
    dataset_dir="VisDrone2019-VID-train",
    output_label_dir="VisDrone2019-VID-train/labels"
)

convert_visdrone_vid_to_yolo(
    dataset_dir="VisDrone2019-VID-val",
    output_label_dir="VisDrone2019-VID-val/labels"
)