import shutil
from pathlib import Path

dataset_dir="VisDrone2019-VID-train"

def flatten_images(dataset_dir, output_image_dir):
    seq_dir   = Path(dataset_dir) / "sequences"
    out_dir   = Path(output_image_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for img_path in sorted(seq_dir.rglob("*.jpg")):
        seq_name = img_path.parent.name
        new_name = f"{seq_name}__{img_path.name}"
        shutil.copy(img_path, out_dir / new_name)

flatten_images("VisDrone2019-VID-train", "VisDrone2019-VID-train/images_flat")
flatten_images("VisDrone2019-VID-val",   "VisDrone2019-VID-val/images_flat")