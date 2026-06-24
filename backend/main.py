import time
import threading
import random
import base64
import math
from pathlib import Path

import mysql.connector
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import cv2
from ultralytics import YOLO
import uvicorn

# LSTM automation module (prediction stage)
from lstm_model import predict_next, train_lstm, save_to_history, save_prediction, get_prediction_accuracy

# Hardware integration
from serial_reader import start_serial_reader

# =========================
# CONFIG
# =========================
PROCESS_INTERVAL = 5  # seconds

DB = {
    "host": "localhost",
    "user": "root",
    "password": "Harsha@2426",
    "database": "ecorescue",
    "autocommit": True
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_IMAGE_PATH = Path(__file__).resolve().parents[1] / "test_images"
WORKSPACE_IMAGE_PATH = PROJECT_ROOT / "test_images"
BASE_IMAGE_PATH = LOCAL_IMAGE_PATH if LOCAL_IMAGE_PATH.exists() else WORKSPACE_IMAGE_PATH
MODEL_PATH = "yolov8n.pt"

# =========================
# APP
# =========================
app = FastAPI(title="EcoRescue YOLO + LSTM Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================
# DB
# =========================
def get_db():
    return mysql.connector.connect(**DB)

# =========================
# YOLO (People Detection Stage)
# =========================
print("🔄 Loading YOLO model...")
yolo = YOLO(MODEL_PATH)
print("✅ YOLO model loaded")

yolo_cache = {}

def pick_image(zone_id: int):
    folder = BASE_IMAGE_PATH / f"zone{zone_id}"
    if not folder.exists():
        return None
    patterns = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.avif")
    images = []
    for pattern in patterns:
        images.extend(folder.glob(pattern))
    return random.choice(images) if images else None

def detect_people(image_path: Path):
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"OpenCV could not read image: {image_path}")

    results = yolo(img, conf=0.3, verbose=False)

    count = 0
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0:  # person class
                count += 1

    annotated = results[0].plot()
    _, buffer = cv2.imencode(".jpg", annotated)
    encoded_img = base64.b64encode(buffer).decode()

    return count, encoded_img

# =========================
# RISK LOGIC
# =========================
def compute_risk(total_people: int, total_beds: int):
    if total_beds <= 0:
        return 150, "Severe"

    ratio = (total_people / total_beds) * 100

    if ratio >= 100:
        return ratio, "Severe"
    elif ratio >= 70:
        return ratio, "Elevated"
    elif ratio >= 40:
        return ratio, "Caution"
    else:
        return ratio, "Safe"

def save_history_safely(zone_id: int, risk_score: float, detected_people: int):
    try:
        save_to_history(zone_id, risk_score, detected_people)
    except Exception as e:
        print(f"ZoneHistory save skipped for zone {zone_id}: {e}")

# =========================
# CORE YOLO LOOP
# =========================
def yolo_loop():
    print("🚀 YOLO detection loop started")

    while True:
        try:
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM Zones")
            zones = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[YOLO] Failed to fetch zones: {e}")
            time.sleep(PROCESS_INTERVAL)
            continue

        for zone in zones:
            # ── use a fresh connection per zone to avoid cursor corruption ──
            try:
                conn = get_db()
                cur = conn.cursor(dictionary=True)
            except Exception as e:
                print(f"[YOLO] DB connect failed for zone {zone['id']}: {e}")
                continue

            try:
                zid = zone["id"]
                zone_name = zone["name"]

                image = pick_image(zid)
                if not image:
                    continue

                # 🔍 Detect people in current image
                people_now, img64 = detect_people(image)

                # 🔁 CUMULATIVE PEOPLE COUNT
                prev_people = zone["detected_people"] or 0
                total_people = prev_people + people_now

                # Safety cap (demo protection)
                max_people = zone["total_beds"] * 2
                total_people = min(total_people, max_people)

                # 🛏️ Bed allocation
                beds_to_allocate = min(people_now, zone["available_beds"])

                cur.execute("""
                    SELECT id, available_beds
                    FROM Shelters
                    WHERE zone_id=%s AND available_beds > 0
                    ORDER BY available_beds DESC
                """, (zid,))
                shelters = cur.fetchall()

                remaining = beds_to_allocate
                for s in shelters:
                    if remaining <= 0:
                        break
                    take = min(s["available_beds"], remaining)
                    cur.execute(
                        "UPDATE Shelters SET available_beds = available_beds - %s WHERE id = %s",
                        (take, s["id"])
                    )
                    remaining -= take

                cur.execute("""
                    SELECT SUM(available_beds) AS beds
                    FROM Shelters WHERE zone_id=%s
                """, (zid,))
                available_beds = cur.fetchone()["beds"] or 0

                # ⚠️ Risk calculation
                risk_score, risk_level = compute_risk(
                    total_people,
                    zone["total_beds"]
                )

                # 🧠 Update Zones table
                cur.execute("""
                    UPDATE Zones SET
                        detected_people=%s,
                        available_beds=%s,
                        risk_score=%s,
                        risk_level=%s
                    WHERE id=%s
                """, (
                    total_people,
                    available_beds,
                    risk_score,
                    risk_level,
                    zid
                ))

                # 🧍 Volunteer assignment
                volunteers = max(1, total_people // 5)

                cur.execute("""
                    INSERT INTO Assignments (zone_id, volunteers_assigned, beds_allocated)
                    VALUES (%s, %s, %s)
                """, (
                    zid,
                    volunteers,
                    beds_to_allocate
                ))

                # 🚨 Alerts
                if risk_level != "Safe":
                    cur.execute("""
                        INSERT INTO Alerts (zone_id, level, message)
                        VALUES (%s, %s, %s)
                    """, (
                        zid,
                        risk_level,
                        f"{risk_level} risk detected in {zone_name}"
                    ))

                # 🖼️ Cache YOLO image for frontend
                yolo_cache[zid] = {
                    "zone_id": zid,
                    "zone_name": zone_name,
                    "people_detected": total_people,   # ← fixed key name
                    "image": img64,
                    "timestamp": time.time()
                }

                # 📊 Save to ZoneHistory for LSTM training (safe — skip if table missing)
                save_history_safely(zid, risk_score, total_people)

                # 🔮 Get LSTM prediction and save it
                try:
                    pred = predict_next(zid)
                    save_prediction(
                        zid,
                        pred["predicted_risk_score"],
                        pred["predicted_level"]
                    )
                except Exception as e:
                    print(f"[LSTM] Prediction save error for zone {zid}: {e}")

            except Exception as e:
                print(f"[YOLO] Error processing zone {zone.get('id')}: {e}")
            finally:
                try:
                    cur.close()
                    conn.close()
                except Exception:
                    pass

        time.sleep(PROCESS_INTERVAL)

# =========================
# API ROUTES
# =========================
@app.get("/api/zones")
def get_zones():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Zones")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.get("/api/zones/{zone_id}")
def get_zone(zone_id: int):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM Zones WHERE id=%s", (zone_id,))
    zone = cur.fetchone()

    cur.execute("""
        SELECT *
        FROM Assignments
        WHERE zone_id=%s
        ORDER BY created_at DESC
        LIMIT 30
    """, (zone_id,))
    history = cur.fetchall()

    cur.close()
    conn.close()
    return {"zone": zone, "history": history}

@app.get("/api/alerts")
def get_alerts():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, z.name AS zone_name
        FROM Alerts a
        JOIN Zones z ON z.id = a.zone_id
        ORDER BY created_at DESC
        LIMIT 10
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.get("/api/yolo-images")
def get_yolo_images():
    return JSONResponse(list(yolo_cache.values()))

@app.get("/api/medical-alerts")
def get_medical_alerts():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT m.*, z.name AS zone_name
        FROM MedicalEmergencies m
        JOIN Zones z ON z.id = m.zone_id
        ORDER BY created_at DESC
        LIMIT 10
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# ════════════════════════════════════════
# LSTM PREDICTION STAGE
# ════════════════════════════════════════

@app.get("/api/predict/{zone_id}")
def predict_zone_risk(zone_id: int):
    """
    LSTM Prediction — returns predicted risk score & level for next period.
    """
    result = predict_next(zone_id)
    return result

@app.get("/api/predict-detailed/{zone_id}")
def predict_zone_detailed(zone_id: int):
    """
    LSTM Prediction with detailed stats (for faculty/reporting).
    Returns: prediction + historical accuracy + training info
    """
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    # Get zone info
    cur.execute("SELECT * FROM Zones WHERE id=%s", (zone_id,))
    zone = cur.fetchone()
    
    # Get historical data count
    cur.execute("""
        SELECT 
            COUNT(*) as total_records,
            AVG(risk_score) as avg_risk,
            MAX(risk_score) as peak_risk,
            MIN(risk_score) as min_risk
        FROM ZoneHistory WHERE zone_id=%s
    """, (zone_id,))
    history = cur.fetchone()
    
    cur.close()
    conn.close()
    
    # Get LSTM prediction
    prediction = predict_next(zone_id)
    
    return {
        "zone_id": zone_id,
        "zone_name": zone["name"],
        "current_status": {
            "detected_people": zone["detected_people"],
            "available_beds": zone["available_beds"],
            "current_risk_score": float(zone["risk_score"]),
            "current_risk_level": zone["risk_level"],
        },
        "lstm_prediction": prediction,
        "training_data": {
            "total_historical_records": history["total_records"],
            "average_risk_score": float(history["avg_risk"]) if history["avg_risk"] else 0,
            "peak_risk_score": float(history["peak_risk"]) if history["peak_risk"] else 0,
            "minimum_risk_score": float(history["min_risk"]) if history["min_risk"] else 0,
            "model_trained": True if history["total_records"] > 10 else False,
        }
    }

@app.post("/api/train/{zone_id}")
def train_zone_model(zone_id: int, background_tasks: BackgroundTasks):
    """
    Trigger LSTM model training for a zone (runs in background).
    """
    background_tasks.add_task(train_lstm, zone_id)
    return {"message": f"LSTM training started for zone {zone_id}"}

@app.post("/api/train/all")
def train_all_zones(background_tasks: BackgroundTasks):
    """
    Train LSTM models for all zones in background.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM Zones")
    zone_ids = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    for zid in zone_ids:
        background_tasks.add_task(train_lstm, zid)
    return {"message": f"LSTM training started for {len(zone_ids)} zones"}

# ════════════════════════════════════════
# PREDICTION TRACKING (FOR PROOF)
# ════════════════════════════════════════

@app.get("/api/prediction-history/{zone_id}")
def get_prediction_history(zone_id: int, limit: int = 50):
    """
    Get recent LSTM predictions for a zone (for proof of predictions changing).
    """
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            id,
            zone_id,
            predicted_risk_score,
            predicted_risk_level,
            actual_risk_score,
            actual_risk_level,
            ROUND(prediction_accuracy, 2) as prediction_accuracy,
            created_at
        FROM LSTMPredictions
        WHERE zone_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (zone_id, limit))
    predictions = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "zone_id": zone_id,
        "total_predictions": len(predictions),
        "predictions": predictions
    }

@app.get("/api/prediction-accuracy/{zone_id}")
def get_zone_prediction_accuracy(zone_id: int, days: int = 1):
    """
    Get prediction accuracy stats for a zone.
    Shows how well the LSTM predictions are performing.
    """
    accuracy = get_prediction_accuracy(zone_id, days)
    return {
        "zone_id": zone_id,
        "period_days": days,
        "total_predictions": accuracy.get("total_predictions", 0),
        "average_accuracy_percent": round(float(accuracy.get("avg_accuracy", 0)) or 0, 2),
        "best_accuracy_percent": round(float(accuracy.get("best_accuracy", 0)) or 0, 2),
        "worst_accuracy_percent": round(float(accuracy.get("worst_accuracy", 0)) or 0, 2),
        "high_accuracy_predictions": accuracy.get("high_accuracy_count", 0),
    }

@app.get("/api/all-predictions")
def get_all_predictions_summary():
    """
    Get summary of all predictions across all zones.
    Perfect for faculty to see overall prediction performance.
    """
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            z.id,
            z.name as zone_name,
            COUNT(lp.id) as total_predictions,
            ROUND(AVG(lp.prediction_accuracy), 2) as avg_accuracy,
            MAX(lp.created_at) as latest_prediction,
            COUNT(CASE WHEN lp.prediction_accuracy > 80 THEN 1 END) as accurate_predictions
        FROM Zones z
        LEFT JOIN LSTMPredictions lp ON z.id = lp.zone_id
        GROUP BY z.id, z.name
        ORDER BY z.id
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "timestamp": time.time(),
        "zones": results
    }



# ════════════════════════════════════════
# SHELTER & BED ALLOCATION ENDPOINTS
# ════════════════════════════════════════

@app.get("/api/shelters")
def get_all_shelters():
    """
    Get all shelters with zone info for bed allocation display.
    """
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, z.name AS zone_name, z.risk_level AS zone_risk_level
        FROM Shelters s
        JOIN Zones z ON z.id = s.zone_id
        ORDER BY z.id, s.available_beds DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.get("/api/bed-allocation")
def get_bed_allocation():
    """
    Get per-zone bed allocation summary for medical emergency display.
    """
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            z.id AS zone_id,
            z.name AS zone_name,
            z.risk_level,
            z.detected_people,
            z.total_beds,
            z.available_beds,
            (z.total_beds - z.available_beds) AS beds_occupied,
            COUNT(m.id) AS medical_cases,
            SUM(CASE WHEN m.status = 'ABNORMAL' THEN 1 ELSE 0 END) AS critical_cases
        FROM Zones z
        LEFT JOIN MedicalEmergencies m ON m.zone_id = z.id
        GROUP BY z.id, z.name, z.risk_level, z.detected_people, z.total_beds, z.available_beds
        ORDER BY z.id
    """)
    zones = cur.fetchall()

    # Get shelters per zone
    result = []
    for zone in zones:
        cur.execute("""
            SELECT id, name, total_beds, available_beds,
                   (total_beds - available_beds) AS beds_used
            FROM Shelters WHERE zone_id = %s
            ORDER BY available_beds DESC
        """, (zone["zone_id"],))
        shelters = cur.fetchall()
        result.append({**zone, "shelters": shelters})

    cur.close()
    conn.close()
    return result


@app.get("/api/zone-history/{zone_id}")
def get_zone_history(zone_id: int, limit: int = 50):
    """
    Return the last <limit> ZoneHistory rows for a zone.
    Used by the frontend to visualise LSTM training data / risk trend.
    """
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, zone_id, risk_score, detected_people, recorded_at
        FROM ZoneHistory
        WHERE zone_id = %s
        ORDER BY recorded_at DESC
        LIMIT %s
    """, (zone_id, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "zone_id": zone_id,
        "total_records": len(rows),
        "history": rows
    }


@app.get("/api/zone-history-all")
def get_all_zone_history():
    """
    Summary of ZoneHistory records per zone — for dashboard overview.
    """
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            z.id AS zone_id,
            z.name AS zone_name,
            COUNT(zh.id) AS total_records,
            MAX(zh.risk_score) AS peak_risk,
            ROUND(AVG(zh.risk_score), 2) AS avg_risk,
            MAX(zh.recorded_at) AS latest_at
        FROM Zones z
        LEFT JOIN ZoneHistory zh ON zh.zone_id = z.id
        GROUP BY z.id, z.name
        ORDER BY z.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


@app.on_event("startup")
def startup():
    threading.Thread(target=yolo_loop, daemon=True).start()
    start_serial_reader()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

