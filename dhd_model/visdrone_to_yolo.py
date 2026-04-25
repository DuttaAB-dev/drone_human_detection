# import os
# from pathlib import Path
# from PIL import Image

# # VisDrone classes (skip 0=ignored, 11=others)
# VISDRONE_CLASSES = {
#     1: 0,   # pedestrian
#     2: 1,   # people
#     3: 2,   # bicycle
#     4: 3,   # car
#     5: 4,   # van
#     6: 5,   # truck
#     7: 6,   # tricycle
#     8: 7,   # awning-tricycle
#     9: 8,   # bus
#     10: 9,  # motor
# }

# def convert_visdrone_to_yolo(img_dir, anno_dir, output_dir):
#     os.makedirs(output_dir, exist_ok=True)

#     for anno_file in Path(anno_dir).glob("*.txt"):
#         img_path = Path(img_dir) / (anno_file.stem + ".jpg")
#         if not img_path.exists():
#             img_path = Path(img_dir) / (anno_file.stem + ".png")

#         img = Image.open(img_path)
#         img_w, img_h = img.size

#         yolo_lines = []
#         with open(anno_file) as f:
#             for line in f:
#                 parts = line.strip().split(",")
#                 if len(parts) < 6:
#                     continue

#                 x, y, w, h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
#                 category = int(parts[5])

#                 # Skip ignored regions (0) and others (11)
#                 if category not in VISDRONE_CLASSES:
#                     continue

#                 # Skip invalid boxes
#                 if w <= 0 or h <= 0:
#                     continue

#                 yolo_class = VISDRONE_CLASSES[category]

#                 # Convert to YOLO normalized format
#                 x_center = (x + w / 2) / img_w
#                 y_center = (y + h / 2) / img_h
#                 norm_w = w / img_w
#                 norm_h = h / img_h

#                 # Clamp to [0, 1]
#                 x_center = min(max(x_center, 0), 1)
#                 y_center = min(max(y_center, 0), 1)
#                 norm_w = min(max(norm_w, 0), 1)
#                 norm_h = min(max(norm_h, 0), 1)

#                 yolo_lines.append(f"{yolo_class} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

#         out_file = Path(output_dir) / (anno_file.stem + ".txt")
#         with open(out_file, "w") as f:
#             f.write("\n".join(yolo_lines))

# # Example usage
# convert_visdrone_to_yolo(
#     img_dir="VisDrone2019-VID-train/images",
#     anno_dir="VisDrone2019-VID-train/annotations",
#     output_dir="VisDrone2019-VID-train/labels"
# )
# 
import os
from PIL import Image
from tqdm import tqdm

def convert_visdrone():
    # Define your paths based on your structure
    base_path = "datasets/VisDrone2019-DET-train"
    img_folder = os.path.join(base_path, "images")
    anno_folder = os.path.join(base_path, "annotations")
    output_folder = os.path.join(base_path, "labels")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # List all annotation files
    anno_files = [f for f in os.listdir(anno_folder) if f.endswith('.txt')]
    
    print(f"Converting {len(anno_files)} files...")

    for label_file in tqdm(anno_files):
        # 1. Match label to image to get dimensions
        img_path = os.path.join(img_folder, label_file.replace('.txt', '.jpg'))
        if not os.path.exists(img_path):
            continue
            
        with Image.open(img_path) as img:
            width, height = img.size

        # 2. Read the raw VisDrone annotations
        with open(os.path.join(anno_folder, label_file), 'r') as f:
            lines = f.readlines()

        yolo_labels = []
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) < 8:
                continue
            
            # VisDrone format: <bbox_left>,<bbox_top>,<bbox_width>,<bbox_height>,<score>,<object_category>,<truncation>,<occlusion>
            l, t, w, h = map(float, parts[:4])
            category = int(parts[5])
            
            # FILTER: 
            # VisDrone 0=ignored, 11=others. 
            # We only want 1 through 10 (Pedestrian to Motor).
            if category < 1 or category > 10:
                continue 

            # CONVERT: 
            # Map 1-10 to 0-9 (0-indexed for YOLO)
            class_id = category - 1 

            # Calculate normalized YOLO coordinates
            # x_center and y_center are the middle of the box
            x_center = (l + w / 2) / width
            y_center = (t + h / 2) / height
            nw = w / width
            nh = h / height
            
            # Bound the values between 0 and 1 just in case of edge noise
            x_center = min(1.0, max(0.0, x_center))
            y_center = min(1.0, max(0.0, y_center))
            nw = min(1.0, max(0.0, nw))
            nh = min(1.0, max(0.0, nh))

            yolo_labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {nw:.6f} {nh:.6f}")

        # 3. Write out the new YOLO formatted file
        with open(os.path.join(output_folder, label_file), 'w') as f:
            f.write('\n'.join(yolo_labels))

if __name__ == "__main__":
    convert_visdrone()
    print("\nConversion complete! Remember to delete labels.cache before training.")