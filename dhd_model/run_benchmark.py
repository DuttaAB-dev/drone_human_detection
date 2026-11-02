# run_benchmark.py
from ultralytics import YOLO
import pandas as pd

def run_evaluations():
    # Load your fine-tuned model
    MODEL_PATH = "models/yolov26s_last_2.pt"
    print(MODEL_PATH)
    model = YOLO(MODEL_PATH)

    # Map all 12 test cases to their respective YAML configs
    EVAL_RUNS = {
        "Dehaze (Degraded)": "yaml_configs/dehaze_degraded.yaml",
        "Dehaze (Restored)": "yaml_configs/dehaze_restored.yaml",
        
        "CLAHE (Degraded)": "yaml_configs/clahe_degraded.yaml",
        "CLAHE (Restored)": "yaml_configs/clahe_restored.yaml",
        
        "Sharpen (Degraded)": "yaml_configs/sharpen_degraded.yaml",
        "Sharpen (Restored)": "yaml_configs/sharpen_restored.yaml",
        
        "Gamma (Degraded)": "yaml_configs/gamma_degraded.yaml",
        "Gamma (Restored)": "yaml_configs/gamma_restored.yaml",
        
        "Bilateral (Degraded)": "yaml_configs/bilateral_degraded.yaml",
        "Bilateral (Restored)": "yaml_configs/bilateral_restored.yaml",
        
        "Combo (Degraded)": "yaml_configs/combo_degraded.yaml",
        "Combo (Restored)": "yaml_configs/combo_restored.yaml",
    }

    results_table = []

    for run_name, yaml_path in EVAL_RUNS.items():
        print(f"\n--- Running Evaluation: {run_name} ---")

        # Run validation
        metrics = model.val(
            data=yaml_path,
            imgsz=1024,
            batch=8,
            device=0,
            verbose=False,
            # agnostic_nms=True # Match the setting used in your detection.py
        )

        results_table.append({
            "Condition": run_name,
            "mAP@0.50": round(float(metrics.box.map50) * 100, 2),
            "mAP@0.50-95": round(float(metrics.box.map) * 100, 2),
            "Precision": round(float(metrics.box.mp) * 100, 2),
            "Recall": round(float(metrics.box.mr) * 100, 2)
        })

    # Print the final comparison
    df = pd.DataFrame(results_table)
    print("\n" + "="*60)
    print("             FILTER EFFECTIVENESS BENCHMARK")
    print("="*60)
    print(df.to_string(index=False))

    # Save to CSV for easy analysis and graphing
    df.to_csv("filter_benchmark_results.csv", index=False)
    print("\nResults successfully saved to 'filter_benchmark_results.csv'")

# Protect the execution loop from multiprocessing recursive spawning
if __name__ == '__main__':
    run_evaluations()
