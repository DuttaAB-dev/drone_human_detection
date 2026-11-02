# /
import sys
import time
import shutil
import psutil
import torch
from pathlib import Path
from ultralytics import YOLO
# Keep your Logger class and callbacks imported/defined here...
class Logger(object):
    """Tees all output to both the terminal and a log file."""
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
    mem = psutil.virtual_memory()
    if mem.percent > 95:
        print(f"\n[MEMORY WARNING] RAM usage is at {mem.percent}%!")
        raise MemoryError(f"Training stopped: High RAM usage ({mem.percent}%)")


def telemetry_epoch_callback(trainer):
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


def backup_full_checkpoint_callback(trainer):
    """
    Copies the just-saved last.pt (which still has its FULL optimizer state
    at this point -- stripping only happens later, once, after the entire
    training loop ends) to a separate filename every epoch. This file is
    never touched by final_eval()'s strip_optimizer(), so even if the run
    ends cleanly (all epochs / patience) or crashes, you always have a
    near-current, fully resumable checkpoint independent of last.pt/best.pt.
    """
    try:
        src = Path(trainer.save_dir) / "weights" / "last.pt"
        dst = Path(trainer.save_dir) / "weights" / "last_with_optimizer_backup.pt"
        if src.exists():
            shutil.copy(src, dst)
    except Exception as e:
        print(f"[backup callback] Warning: could not back up checkpoint: {e}")

def resume_training():
    print("[RESUMING RUN] Loading checkpoint with optimizer intact...")
    
    # 1. Point to your backup checkpoint (or epoch5.pt if last is broken)
    checkpoint_path = "/var/home/anirban/MyProjects/drone_human_detection/dhd_model/runs/detect/runs/detect/visdrone_fresh_full_60/weights/last.pt"
    
    # 2. Load the model from the checkpoint
    model = YOLO(checkpoint_path)

    # 3. Re-register your custom telemetry and memory callbacks
    model.add_callback("on_train_batch_start", check_memory_callback)
    model.add_callback("on_train_epoch_end", telemetry_epoch_callback)
    model.add_callback("on_model_save", backup_full_checkpoint_callback)

    try:
        # 4. Call train with resume=True. 
        # Note: YOLO will automatically reuse the configurations from the original args.yaml
        model.train(resume=True)
        
    except MemoryError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    log_file = f"training_process_resume_{int(time.time())}.log"
    sys.stdout = Logger(log_file, sys.stdout)
    sys.stderr = Logger(log_file, sys.stderr)

    resume_training()
