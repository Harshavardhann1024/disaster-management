# yolo_demo.py — Real‑time YOLO detection and DB update demo
"""
This script demonstrates a minimal real‑time workflow for the EcoRescue project:
1. Capture frames from a webcam (or video file).
2. Run YOLOv8 object detection (using the `ultralytics` package).
3. Insert each detection into the MySQL `Detections` table with a timestamp and zone identifier.
The ML‑model part (risk prediction) will be presented later – this file focuses on the
image‑capture / DB‑update pipeline required for tomorrow's demo.
"""

import cv2
import datetime
import os
from pathlib import Path

# YOLO model – ultralytics YOLOv8 (small model for fast demo)
# Ensure the package is installed: `pip install ultralytics`
from ultralytics import YOLO

# Re‑use the same DB configuration as lstm_model.py
# Import the helper that lazily creates a connection
try:
    from lstm_model import _get_db  # noqa: F401
except Exception as e:
    raise ImportError("Unable to import DB helper from lstm_model. Ensure lstm_model.py is in the PYTHONPATH.") from e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_PATH = "yolov8s.pt"  # pretrained small model – will be downloaded automatically
ZONE_ID = 1                # demo zone; change as needed

# Create a simple table for detections if it does not exist.
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS Detections (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    zone_id INT NOT NULL,
    class_name VARCHAR(255) NOT NULL,
    confidence FLOAT NOT NULL,
    detected_at DATETIME NOT NULL
) ENGINE=INNODB;
"""


def ensure_table():
    conn = _get_db()
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()


def insert_detection(class_name: str, confidence: float):
    conn = _get_db()
    cur = conn.cursor()
    sql = "INSERT INTO Detections (zone_id, class_name, confidence, detected_at) VALUES (%s, %s, %s, %s)"
    cur.execute(sql, (ZONE_ID, class_name, confidence, datetime.datetime.utcnow()))
    conn.commit()
    cur.close()
    conn.close()


def run_yolo_demo():
    # Load the model – it will be downloaded on first run
    model = YOLO(MODEL_PATH)

    # Open default webcam (device 0). Change to a video file path for a pre‑recorded demo.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Unable to open webcam. Verify that a camera is connected.")

    print("[YOLO Demo] Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run detection – results is a list with a single element for one image
        results = model(frame)
        # results[0].boxes contains the detections
        boxes = results[0].boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls_id]
            # Insert detection into DB
            insert_detection(class_name, conf)
            # Draw bounding box for visual feedback
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 255, 0), 2)
            label = f"{class_name} {conf:.2f}"
            cv2.putText(frame, label, (xyxy[0], xyxy[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("YOLO Real‑time Demo", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    ensure_table()
    run_yolo_demo()
