from ultralytics import YOLO

model = YOLO("best.pt")
results = model.predict(source="data/raw_dataset/biological/biological_13.jpg", save=True, conf=0.25, iou=0.45, max_det=1000)
print(results[0].boxes)