

# from ultralytics import YOLO

# if __name__ == '__main__':
#     model = YOLO("yolo11n.pt")
#     model.train(
#         data="visdrone_vid.yaml",
#         imgsz=640,
#         batch=8,
#         workers=4,
#         amp=True,
#     )
#
# import os
# import sys
# from ultralytics import YOLO
# import time
# import psutil
# import torch

# class Logger(object):
#     """
#     A class that 'tees' all output to both the terminal and a log file.
#     """
#     def __init__(self, filename="training_process.log", stream=sys.stdout):
#         self.terminal = stream
#         self.log = open(filename, "a", encoding="utf-8")

#     def write(self, message):
#         self.terminal.write(message)
#         self.log.write(message)
#         self.log.flush()

#     def flush(self):
#         # This flush method is needed for python 3 compatibility.
#         self.terminal.flush()
#         self.log.flush()

# def check_memory_callback(trainer):
#     """
#     Check system memory usage and stop training if it exceeds 90%.
#     """
#     mem = psutil.virtual_memory()
#     if mem.percent > 95:
#         print(f"\n[MEMORY WARNING] RAM usage is at {mem.percent}%!")
#         print("Stopping training to prevent system crash...")
#         # Raising an exception is the safest way to break out of the internal C++ training loop
#         raise MemoryError(f"Training stopped: High RAM usage ({mem.percent}%)")

# def train_visdrone_det():
#     # 1. Path Setup
#     # Path to the yaml we just created
#     yaml_path = os.path.join(os.getcwd(), "visdrone_vid.yaml")

#     # 2. Hardware Management
#     # Your 8GB NVIDIA card is perfect for 's' or 'm' models
#     device = 0 if torch.cuda.is_available() else "cpu"

#     # 3. Load Model
#     # Starting with your existing yolo11s.pt
#     model = YOLO("models/yolov26s_trained_v1_best.pt")

#     # 4. Add the memory check callback
#     model.add_callback("on_train_batch_start", check_memory_callback)

#      # 5. Training
#     try:
#             model.train(
#                 data=yaml_path,
#                 epochs=50,
#                 patience=15,
#                 imgsz=1024,          # High-res for those tiny VisDrone objects
#                 batch=6,
#                 device=device,
#                 workers=7,           # Reduced from 4 to 2 for better RAM safety
#                 project="runs/detect",
#                 name="visdrone_det_training",
#                 exist_ok=True,
#                 amp=True,
#                 mosaic=1.0,
#                 cache=False
#             )
#     except MemoryError as e:
#             print(f"Error: {e}")
#     except Exception as e:
#             print(f"An unexpected error occurred: {e}")


# if __name__ == "__main__":
#     log_file = f"training_process_{time.time()}.log"
#     sys.stdout = Logger(log_file, sys.stdout)
#     sys.stderr = Logger(log_file, sys.stderr)

#     train_visdrone_det()


# """Second iteration"""
# import os
# import sys
# import time
# import psutil
# import torch
# from pathlib import Path
# from ultralytics import YOLO


# class Logger(object):
#     """
#     A class that 'tees' all output to both the terminal and a log file.
#     Filters out progress bar noise (\r) from the text file to keep it clean.
#     """
#     def __init__(self, filename="training_process.log", stream=sys.stdout):
#         self.terminal = stream
#         self.log = open(filename, "a", encoding="utf-8")

#     def write(self, message):
#         self.terminal.write(message)
#         if '\r' in message and '\n' not in message:
#             return
#         clean_message = message.replace('\r', '')
#         if clean_message:
#             self.log.write(clean_message)
#             self.log.flush()

#     def flush(self):
#         self.terminal.flush()
#         self.log.flush()


# def check_memory_callback(trainer):
#     """
#     Safeguard: Check system memory usage and stop training if it exceeds 95%.
#     """
#     mem = psutil.virtual_memory()
#     if mem.percent > 95:
#         print(f"\n[MEMORY WARNING] RAM usage is at {mem.percent}%!")
#         print("Stopping training to prevent system crash...")
#         raise MemoryError(f"Training stopped: High RAM usage ({mem.percent}%)")


# def telemetry_epoch_callback(trainer):
#     """
#     Telemetry: Logs detailed system resource metrics automatically at the conclusion of every epoch.
#     """
#     epoch = trainer.epoch + 1
#     epochs = trainer.epochs
#     mem = psutil.virtual_memory()
#     cpu_pct = psutil.cpu_percent()

#     print(f"\n--- TELEMETRY: End of Epoch {epoch}/{epochs} ---")
#     print(f"System RAM Usage: {mem.percent}% ({mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB)")
#     print(f"CPU Utilization: {cpu_pct}%")

#     if torch.cuda.is_available():
#         vram_allocated = torch.cuda.memory_allocated(0) / (1024**3)
#         vram_reserved = torch.cuda.memory_reserved(0) / (1024**3)
#         print(f"GPU VRAM Allocated: {vram_allocated:.2f} GB | Reserved: {vram_reserved:.2f} GB")

#     if hasattr(trainer, 'optimizer') and trainer.optimizer.param_groups:
#         current_lr = trainer.optimizer.param_groups[0]['lr']
#         print(f"Active Learning Rate (LR): {current_lr:.6f}")
#     print("-------------------------------------------\n")


# def prepare_subsampled_dataset(stride=5):
#     """
#     Builds a frame-subsampled training set via flat symlinks (kept exactly as you
#     wrote it -- this is the part that fixed the "zero labels found" bug from the
#     last run). Untouched from your version.
#     """
#     base_dir = Path(os.getcwd())
#     flat_img_dir = base_dir / "datasets/VisDrone2019-VID-train/images"
#     val_img_dir = base_dir / "datasets/VisDrone2019-VID-val/images"

#     if not flat_img_dir.exists():
#         raise FileNotFoundError(f"Could not find flat image directory at: {flat_img_dir}")

#     all_images = sorted(list(flat_img_dir.glob("*.jpg")))

#     sequences = {}
#     for img_path in all_images:
#         seq_name = img_path.name.split("__")[0]
#         sequences.setdefault(seq_name, []).append(img_path)

#     subsampled_paths = []
#     for seq_name, paths in sequences.items():
#         subsampled_paths.extend(paths[::stride])

#     train_txt_path = base_dir / "train_subsampled.txt"
#     with open(train_txt_path, "w") as f:
#         for p in subsampled_paths:
#             f.write(f"{os.path.abspath(p)}\n")

#     print(f"\n[SUBSAMPLE] Kept {len(subsampled_paths)}/{len(all_images)} flat frames (stride={stride}) -> {train_txt_path.name}")

#     for cache_file in base_dir.rglob("*.cache"):
#         try:
#             cache_file.unlink()
#         except Exception:
#             pass

#     subsampled_yaml_content = f"""
# path: {base_dir.resolve()}
# train: {train_txt_path.name}
# val: {val_img_dir.relative_to(base_dir)}

# nc: 10
# names:
#   0: pedestrian
#   1: people
#   2: bicycle
#   3: car
#   4: van
#   5: truck
#   6: tricycle
#   7: awning-tricycle
#   8: bus
#   9: motor
# """
#     yaml_path = base_dir / "visdrone_vid_subsampled.yaml"
#     with open(yaml_path, "w") as f:
#         f.write(subsampled_yaml_content.strip())

#     return str(yaml_path)


# def train_visdrone_det():
#     # 1. Prepare data using flat symlink strings (this part works -- keep it)
#     try:
#         yaml_path = prepare_subsampled_dataset(stride=5)
#     except Exception as e:
#         print(f"Dataset preparation failed: {e}")
#         return

#     # 2. Hardware Management
#     device = 0 if torch.cuda.is_available() else "cpu"

#     # 3. Load Model base
#     model = YOLO("models/yolov26s_trained_v1_best.pt")

#     # 4. Attach Callbacks
#     model.add_callback("on_train_batch_start", check_memory_callback)
#     model.add_callback("on_train_epoch_end", telemetry_epoch_callback)

#     # 5. Training Loop
#     #
#     # NOTE: labels are now matching correctly (train_batch*.jpg shows real boxes
#     # again), so the overfitting we're seeing this run is real, not a data bug --
#     # it's the same "best epoch is 1, then degrades" pattern from your very first
#     # run, because these hyperparameters are the original ones that caused it
#     # (lr0=0.0005, mosaic=1.0, mixup=0.15, copy_paste=0.1, warmup_epochs=1.0).
#     # Re-applying the fine-tuning stabilization below, on top of your now-working
#     # dataset pipeline.
#     try:
#         model.train(
#             data=yaml_path,
#             epochs=30,
#             patience=8,
#             imgsz=1024,
#             batch=6,
#             device=device,
#             workers=4,
#             project="runs/detect",
#             name="visdrone_vid_finetune",
#             exist_ok=True,
#             amp=True,
#             cache="disk",               # safer than True given 16GB system RAM;
#                                          # faster than False given 8GB VRAM ceiling

#             # --- Fine-tuning stabilization ---
#             optimizer="AdamW",
#             lr0=0.0001,                  # lowered from 0.0005 -- gentler step for
#                                          # fine-tuning an already-converged checkpoint
#             lrf=0.01,
#             cos_lr=True,                 # smoother decay
#             warmup_epochs=2.0,

#             # --- Reduced augmentation for a short fine-tune ---
#             mosaic=0.5,                  # was 1.0
#             mixup=0.0,                   # was 0.15 -- off for fine-tuning
#             copy_paste=0.0,              # was 0.1 -- off for fine-tuning
#             close_mosaic=5,              # disable mosaic entirely for final epochs
#         )
#     except MemoryError as e:
#         print(f"Error: {e}")
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")


# if __name__ == "__main__":
#     log_file = f"training_process_{int(time.time())}.log"
#     sys.stdout = Logger(log_file, sys.stdout)
#     sys.stderr = Logger(log_file, sys.stderr)

#     train_visdrone_det()

"""Third iteration"""


import os
import sys
import time
import psutil
import torch
from pathlib import Path
from ultralytics import YOLO


class Logger(object):
    """
    A class that 'tees' all output to both the terminal and a log file.
    Filters out progress bar noise (\r) from the text file to keep it clean.
    """
    def __init__(self, filename="training_process.log", stream=sys.stdout):
        self.terminal = stream
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        if '\r' in message and '\n' not in message:
            return
        clean_message = message.replace('\r', '')
        if clean_message:
            self.log.write(clean_message)
            self.log.flush()

    def flush(self):
        self.terminal.flush()
        self.log.flush()


def check_memory_callback(trainer):
    """
    Safeguard: Check system memory usage and stop training if it exceeds 95%.
    """
    mem = psutil.virtual_memory()
    if mem.percent > 95:
        print(f"\n[MEMORY WARNING] RAM usage is at {mem.percent}%!")
        print("Stopping training to prevent system crash...")
        raise MemoryError(f"Training stopped: High RAM usage ({mem.percent}%)")


def telemetry_epoch_callback(trainer):
    """
    Telemetry: Logs detailed system resource metrics automatically at the conclusion of every epoch.
    """
    epoch = trainer.epoch + 1
    epochs = trainer.epochs
    mem = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent()

    print(f"\n--- TELEMETRY: End of Epoch {epoch}/{epochs} ---")
    print(f"System RAM Usage: {mem.percent}% ({mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB)")
    print(f"CPU Utilization: {cpu_pct}%")

    if torch.cuda.is_available():
        vram_allocated = torch.cuda.memory_allocated(0) / (1024**3)
        vram_reserved = torch.cuda.memory_reserved(0) / (1024**3)
        print(f"GPU VRAM Allocated: {vram_allocated:.2f} GB | Reserved: {vram_reserved:.2f} GB")

    if hasattr(trainer, 'optimizer') and trainer.optimizer.param_groups:
        current_lr = trainer.optimizer.param_groups[0]['lr']
        print(f"Active Learning Rate (LR): {current_lr:.6f}")
    print("-------------------------------------------\n")


def prepare_full_joint_dataset():
    """
    Generates a dynamic mixed YAML configuration that anchors training using 
    both the full VisDrone-DET static distribution and the full VisDrone-VID sequence files.
    """
    base_dir = Path(os.getcwd())
    
    det_train_img_dir = base_dir / "datasets/VisDrone2019-DET-train/images"
    det_val_img_dir = base_dir / "datasets/VisDrone2019-DET-val/images"
    vid_train_img_dir = base_dir / "datasets/VisDrone2019-VID-train/images"
    vid_val_img_dir = base_dir / "datasets/VisDrone2019-VID-val/images"

    # Paths validation check
    for path_check in [det_train_img_dir, vid_train_img_dir, vid_val_img_dir]:
        if not path_check.exists():
            raise FileNotFoundError(f"Missing required execution dataset path component: {path_check}")

    # Force delete old system index .cache items to prevent path conflicts
    print("[CLEANUP] Stripping invalid configuration cache footprints...")
    for cache_file in base_dir.rglob("*.cache"):
        try:
            cache_file.unlink()
        except Exception:
            pass

    # Build multi-dataset directory configuration paths
    joint_yaml_content = f"""
path: {base_dir.resolve()}
train:
  - {det_train_img_dir.relative_to(base_dir)}  # Full baseline static detection dataset
  - {vid_train_img_dir.relative_to(base_dir)}  # Full complete video sequence frame dataset

val:
  - {det_val_img_dir.relative_to(base_dir)}    # Static validation set
  - {vid_val_img_dir.relative_to(base_dir)}    # Video tracking validation set

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
    yaml_path = base_dir / "visdrone_full_joint.yaml"
    with open(yaml_path, "w") as f:
        f.write(joint_yaml_content.strip())
        
    print(f"[YAML CREATION] Fresh multi-dataset configuration stored -> {yaml_path.name}")
    return str(yaml_path)

def backup_full_checkpoint_callback(epoch, model):
    try:
        src = Path(trainer)


def train_visdrone_det():
    # 1. Generate full joint distribution profile mapping files
    try:
        yaml_path = prepare_full_joint_dataset()
    except Exception as e:
        print(f"Dataset preparation failed: {e}")
        return

    # 2. Hardware Management
    device = 0 if torch.cuda.is_available() else "cpu"

    # 3. Load clean, stock COCO-pretrained weights to discard baseline errors
    print("[MODEL INITIALIZATION] Initializing training fresh using stock yolo26s.pt...")
    model = YOLO("yolo26s.pt")

    # 4. Attach Guardrail and Monitoring Callbacks
    model.add_callback("on_train_batch_start", check_memory_callback)
    model.add_callback("on_train_epoch_end", telemetry_epoch_callback)
    model.add_callback("on_model_save", backup_full_checkpoint_callback)

    # 5. Training Loop
    try:
        model.train(
            data=yaml_path,
            epochs=60,                   # Balanced schedule length for combined sets from scratch
            patience=15,                 # Healthy early stopping window grounded by dual validation sets
            imgsz=1024,                  # Maximizes image space for small aerial object detection
            batch=6,                     # Upper bound safe boundary for your 8GB VRAM footprint
            device=device,
            workers=4,                   # Hard data worker count cap for 16GB system RAM stability
            project="runs/detect",
            name="visdrone_fresh_60_joint",
            exist_ok=True,
            amp=True,
            cache="disk",               # Prevents system RAM bottlenecks while accelerating pipeline load speeds
            save_period=5,
            # --- Stable Standard AdamW Hyperparameters ---
            optimizer="AdamW",
            lr0=0.001,                   # Stable starting rate for standard model co-training setups
            lrf=0.01,
            cos_lr=True,                 
            warmup_epochs=3.0,           # Gradual warm up period for stable gradient derivation

            # --- High Regularization Layer Enforcements (Blocks Memorization) ---
            mosaic=1.0,                  
            mixup=0.15,                  
            copy_paste=0.1,              
            close_mosaic=10,             # Shuts down mosaics during the final 10 epochs for structural fine-tuning
        )
    except MemoryError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    log_file = f"training_process_{int(time.time())}.log"
    sys.stdout = Logger(log_file, sys.stdout)
    sys.stderr = Logger(log_file, sys.stderr)

    train_visdrone_det()    