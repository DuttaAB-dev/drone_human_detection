# benchmark_preprocessor.py
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm
from services.filters import preprocess_image

# Directories
VAL_IMG_DIR = Path("datasets/VisDrone2019-DET-val/images")
OUTPUT_BASE_DIR = Path("datasets/VisDrone_Filtered_Val")

# --- 1. Synthetic Degradation Functions ---

def add_synthetic_haze(image, t=0.5, A=220):
    """
    Simulates haze via the Atmospheric Scattering Model.
    """
    hazy = image.astype(np.float32) * t + A * (1 - t)
    return np.clip(hazy, 0, 255).astype(np.uint8)

def reduce_contrast(image, factor=0.4):
    """Compresses the histogram towards 127 (gray) to simulate flat lighting."""
    gray_image = np.full(image.shape, 127.0, dtype=np.float32)
    low_contrast = image.astype(np.float32) * factor + gray_image * (1 - factor)
    return np.clip(low_contrast, 0, 255).astype(np.uint8)

def add_synthetic_blur(image, ksize=(11, 11)):
    """Applies Gaussian smoothing to simulate out-of-focus or motion blur."""
    return cv2.GaussianBlur(image, ksize, 0)

def reduce_exposure(image, gamma=2.5):
    """Simulates underexposure using a reverse gamma curve."""
    table = np.array([((i / 255.0) ** gamma) * 255 for i in np.arange(0, 256)]).astype(np.uint8)
    return cv2.LUT(image, table)

def add_gaussian_noise(image, mean=0, std=25):
    """Simulates camera sensor noise."""
    noise = np.random.normal(mean, std, image.shape).astype(np.float32)
    noisy = image.astype(np.float32) + noise
    return np.clip(noisy, 0, 255).astype(np.uint8)

def combo_degrade(image):
    return add_synthetic_blur(reduce_contrast(image))


# --- 2. Evaluation Mapping ---
# Maps a test scenario to its specific degradation function and the filter meant to fix it.
TEST_CASES = {
    "dehaze_eval": {"degrade": add_synthetic_haze, "filters": ["dehaze"]},
    "clahe_eval": {"degrade": reduce_contrast, "filters": ["clahe"]},
    "sharpen_eval": {"degrade": add_synthetic_blur, "filters": ["sharpen"]},
    "gamma_eval": {"degrade": reduce_exposure, "filters": ["gamma-correction"]},
    "bilateral_eval": {"degrade": add_gaussian_noise, "filters": ["bilateral-filter"]},
    "combo_eval": {"degrade": combo_degrade, "filters": ["clahe", "sharpen"]},
}


# --- 3. Dataset Generation Loop ---
def generate_filtered_datasets():
    for name, config in TEST_CASES.items():
        print(f"\nGenerating evaluation sets for: '{name}'...")

        # Create TWO folders to compare "Without Filter" vs "With Filter"
        # Define paths
        degraded_img_dir = OUTPUT_BASE_DIR / name / "degraded_raw" / "images"
        restored_img_dir = OUTPUT_BASE_DIR / name / "restored" / "images"

        degraded_lbl_dir = OUTPUT_BASE_DIR / name / "degraded_raw" / "labels"
        restored_lbl_dir = OUTPUT_BASE_DIR / name / "restored" / "labels"

        # Create directories
        for d in [degraded_img_dir, restored_img_dir, degraded_lbl_dir, restored_lbl_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Symlink the original validation labels to both new directories
        original_labels_dir = Path("datasets/VisDrone2019-DET-val/labels")
        for label_path in original_labels_dir.glob("*.txt"):
            # Symlink for degraded
            deg_lbl_target = degraded_lbl_dir / label_path.name
            if not deg_lbl_target.exists():
                deg_lbl_target.symlink_to(label_path.resolve())

            # Symlink for restored
            rest_lbl_target = restored_lbl_dir / label_path.name
            if not rest_lbl_target.exists():
                rest_lbl_target.symlink_to(label_path.resolve())

        # degraded_dir.mkdir(parents=True, exist_ok=True)
        # restored_dir.mkdir(parents=True, exist_ok=True)

        for img_path in tqdm(list(VAL_IMG_DIR.glob("*.jpg"))):
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            # Step A: Apply environmental distortion
            degraded_img = config["degrade"](img)
            cv2.imwrite(str(degraded_img_dir / img_path.name), degraded_img)

            # Step B: Apply the specific restoration pipeline to the degraded image
            restored_img = preprocess_image(degraded_img, config["filters"])
            cv2.imwrite(str(restored_img_dir / img_path.name), restored_img)

if __name__ == "__main__":
    generate_filtered_datasets()
