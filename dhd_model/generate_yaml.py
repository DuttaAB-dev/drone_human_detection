import os
from pathlib import Path

# Base configuration strings
BASE_PATH = "/var/home/anirban/MyProjects/drone_human_detection/dhd_model"
CLASSES_CONFIG = """
nc: 10
names:
  0: pedestrian
  1: people
  2: bicycle
  3: car
  4: van
  5: truck
  6: tricycle
  7: awning-tricycle
  8: bus
  9: motor
"""

# The test cases defined in benchmark_preprocessor.py
TEST_CASES = [
    "dehaze_eval",
    "clahe_eval",
    "sharpen_eval",
    "gamma_eval",
    "bilateral_eval",
    "combo_eval"
]

def generate_yaml_files():
    output_dir = Path("yaml_configs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for case in TEST_CASES:
        prefix = case.split("_")[0]
        
        # 1. Generate Degraded YAML
        degraded_val_path = f"datasets/VisDrone_Filtered_Val/{case}/degraded_raw/images"
        degraded_content = f"path: {BASE_PATH}\ntrain: {degraded_val_path}\nval: {degraded_val_path}\n{CLASSES_CONFIG}"
        
        with open(output_dir / f"{prefix}_degraded.yaml", "w") as f:
            f.write(degraded_content)
            
        # 2. Generate Restored YAML
        restored_val_path = f"datasets/VisDrone_Filtered_Val/{case}/restored/images"
        restored_content = f"path: {BASE_PATH}\ntrain: {restored_val_path}\nval: {restored_val_path}\n{CLASSES_CONFIG}"
        
        with open(output_dir / f"{prefix}_restored.yaml", "w") as f:
            f.write(restored_content)
            
    print(f"Successfully regenerated 12 YAML configs in {output_dir.resolve()}")

if __name__ == "__main__":
    generate_yaml_files()
