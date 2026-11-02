import os
from pathlib import Path

def convert_det_annotations(base_dir):
    """
    Validates and indexes the VisDrone-DET annotations with proper 0-based indexing.
    VisDrone-DET images and annotations are usually stored under:
    datasets/VisDrone2019-DET-train/images and /annotations
    """
    base_path = Path(base_dir)
    det_train_img_dir = base_path / "datasets/VisDrone2019-DET-train/images"
    det_train_anno_dir = base_path / "datasets/VisDrone2019-DET-train/annotations"
    det_train_label_dir = base_path / "datasets/VisDrone2019-DET-train/labels"
    
    det_val_img_dir = base_path / "datasets/VisDrone2019-DET-val/images"
    det_val_anno_dir = base_path / "datasets/VisDrone2019-DET-val/annotations"
    det_val_label_dir = base_path / "datasets/VisDrone2019-DET-val/labels"

    def process_split(img_dir, anno_dir, label_dir):
        if not img_dir.exists() or not anno_dir.exists():
            print(f"[WARNING] Skipping split, directory not found: {img_dir}")
            return False
        
        label_dir.mkdir(parents=True, exist_ok=True)
        img_paths = list(img_dir.glob("*.jpg"))
        
        for img_path in img_paths:
            anno_path = anno_dir / f"{img_path.stem}.txt"
            label_path = label_dir / f"{img_path.stem}.txt"
            
            if not anno_path.exists():
                # Write an empty file for negative background samples
                with open(label_path, "w") as f:
                    pass
                continue
                
            try:
                import cv2
                img = cv2.imread(str(img_path))
                h, w, _ = img.shape
            except ImportError:
                w, h = 1920, 1080 
                
            yolo_lines = []
            with open(anno_path, "r") as f:
                for line in f:
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) < 6:
                        continue
                    
                    x_min = float(parts[0])
                    y_min = float(parts[1])
                    box_w = float(parts[2])
                    box_h = float(parts[3])
                    category = int(parts[5])
                    
                    # Ignore background (0) or ignored regions (11) from raw VisDrone formats
                    if category == 0 or category == 11:
                        continue
                        
                    # Shift 1-10 down to 0-9 to comply with standard YOLO indexing limits
                    cls_id = category - 1
                    
                    # Calculate standard YOLO center coordinates normalized
                    x_center = (x_min + box_w / 2.0) / w
                    y_center = (y_min + box_h / 2.0) / h
                    norm_w = box_w / w
                    norm_h = box_h / h
                    
                    yolo_lines.append(f"{cls_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")
            
            with open(label_path, "w") as out_f:
                out_f.write("\n".join(yolo_lines))
                
        print(f"[SUCCESS] Processed {len(img_paths)} files into {label_dir}")
        return True

    print("Converting VisDrone-DET Training split...")
    process_split(det_train_img_dir, det_train_anno_dir, det_train_label_dir)
    print("Converting VisDrone-DET Validation split...")
    process_split(det_val_img_dir, det_val_anno_dir, det_val_label_dir)

if __name__ == "__main__":
    convert_det_annotations(os.getcwd())