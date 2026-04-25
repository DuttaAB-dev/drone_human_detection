

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
import os
import sys
from ultralytics import YOLO
import psutil
import torch

class Logger(object):
    """
    A class that 'tees' all output to both the terminal and a log file.
    """
    def __init__(self, filename="training_process.log", stream=sys.stdout):
        self.terminal = stream
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        # This flush method is needed for python 3 compatibility.
        self.terminal.flush()
        self.log.flush()
        
def check_memory_callback(trainer):
    """
    Check system memory usage and stop training if it exceeds 90%.
    """
    mem = psutil.virtual_memory()
    if mem.percent > 95:
        print(f"\n[MEMORY WARNING] RAM usage is at {mem.percent}%!")
        print("Stopping training to prevent system crash...")
        # Raising an exception is the safest way to break out of the internal C++ training loop
        raise MemoryError(f"Training stopped: High RAM usage ({mem.percent}%)")

def train_visdrone_det():
    # 1. Path Setup
    # Path to the yaml we just created
    yaml_path = os.path.join(os.getcwd(), "visdrone_custom.yaml")
    
    # 2. Hardware Management
    # Your 8GB NVIDIA card is perfect for 's' or 'm' models
    device = 0 if torch.cuda.is_available() else "cpu"
    
    # 3. Load Model
    # Starting with your existing yolo11s.pt
    model = YOLO("yolo26s.pt")
    
    # 4. Add the memory check callback
    model.add_callback("on_train_batch_start", check_memory_callback)
    
     # 5. Training
    try:
            model.train(
                data=yaml_path,
                epochs=100,
                imgsz=1024,          # High-res for those tiny VisDrone objects
                batch=6,             
                device=device,
                workers=2,           # Reduced from 4 to 2 for better RAM safety
                project="runs/detect",
                name="visdrone_det_training",
                exist_ok=True,
                amp=True,            
                mosaic=1.0,          
                cache=False          
            )
    except MemoryError as e:
            print(f"Error: {e}")
    except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    log_file = "training_process.log"
    sys.stdout = Logger(log_file, sys.stdout)
    sys.stderr = Logger(log_file, sys.stderr)
       
    train_visdrone_det()


