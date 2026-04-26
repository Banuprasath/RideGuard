from ultralytics import YOLO
import os
import shutil

DATA_YAML   = "New-Model/data.yaml"
BASE_MODEL  = "yolov8n.pt"   # nano = fastest | yolov8s.pt = better accuracy
EPOCHS      = 50
BATCH       = 8              # reduce to 4 if out-of-memory error
IMG_SIZE    = 640
OUTPUT_DIR  = "helmet_training"
RUN_NAME    = "run1"

print("=" * 50)
print("HELMET MODEL TRAINING")
print("=" * 50)
print(f"Model   : {BASE_MODEL}")
print(f"Epochs  : {EPOCHS}")
print(f"Batch   : {BATCH}")
print(f"Data    : {DATA_YAML}")
print("=" * 50)

model = YOLO(BASE_MODEL)

model.train(
    data=DATA_YAML,
    epochs=EPOCHS,
    imgsz=IMG_SIZE,
    batch=BATCH,
    workers=2,
    device=0,        # 0 = GPU | 'cpu' = CPU only
    project=OUTPUT_DIR,
    name=RUN_NAME,
    resume=False,    # set True to resume interrupted training
    patience=10,     # stop early if no improvement for 10 epochs
    save=True,
    verbose=True
)

# Auto copy best.pt to Live_location root
src = os.path.join(OUTPUT_DIR, RUN_NAME, "weights", "best.pt")
dst = "best.pt"

if os.path.exists(src):
    shutil.copy(src, dst)
    print("\n" + "=" * 50)
    print("Training complete!")
    print(f"best.pt copied to: {dst}")
    print("You can now run Merging_module_3.py")
    print("=" * 50)
else:
    print(f"\nTraining done but best.pt not found at: {src}")
    print("Check manually in helmet_training/run1/weights/")
