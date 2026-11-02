import sys
import time
import shutil
import psutil
import torch
from pathlib import Path
from ultralytics import YOLO


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


def fresh_train_60():
    print("[FRESH RUN] Training yolo26s.pt from scratch for 60 epochs,")
    print("matching the original args.yaml hyperparameters.")
    print("save_period=5 preserves optimizer-intact periodic snapshots.")
    print("A backup callback also keeps a near-current full checkpoint")
    print("that survives the end-of-training optimizer stripping.\n")

    model = YOLO("yolo26s.pt")

    model.add_callback("on_train_batch_start", check_memory_callback)
    model.add_callback("on_train_epoch_end", telemetry_epoch_callback)
    model.add_callback("on_model_save", backup_full_checkpoint_callback)

    try:
        model.train(
            data="/var/home/anirban/MyProjects/drone_human_detection/dhd_model/visdrone_full_joint.yaml",
            epochs=60,
            patience=15,
            imgsz=1024,
            batch=6,
            device=0,
            workers=4,
            project="runs/detect",
            name="visdrone_fresh_full_60",
            exist_ok=True,
            amp=True,
            cache="disk",
            save_period=5,          # KEY: periodic epochN.pt snapshots, never stripped of optimizer

            # optimizer="AdamW",
            lr0=0.01,
            lrf=0.01,
            # momentum=0.937,
            # weight_decay=0.0005,
            cos_lr=True,
            warmup_epochs=3.0,
            # warmup_momentum=0.8,
            # warmup_bias_lr=0.1,

            # box=7.5,
            # cls=0.5,
            # dfl=1.5,

            # hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
            # translate=0.1, scale=0.5, fliplr=0.5,
            mosaic=1.0,
            # mixup=0.15, copy_paste=0.1,
            # copy_paste_mode="flip",
            # auto_augment="randaugment", erasing=0.4,
            close_mosaic=10,

            # deterministic=True,
            # seed=0,
        )
    except MemoryError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    log_file = f"training_process_fresh60_{int(time.time())}.log"
    sys.stdout = Logger(log_file, sys.stdout)
    sys.stderr = Logger(log_file, sys.stderr)

    fresh_train_60()
