import time, threading, random, base64, math
from pathlib import Path

import mysql.connector
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import cv2
from ultralytics import YOLO
import uvicorn

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

BASE_IMAGE_PATH = Path(r"C:\ECO RESCUE\test_images")
MODEL_PATH = "yolov8n.pt"

# =========================
# APP
# =========================
app = FastAPI(title="EcoRescue YOLO Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# =========================
# DB UTILS
# =========================
def get_db():
    return mysql.connector.connect(**DB)

# =========================
# YOLO INIT
# =========================
print("🔄 Loading YOLO model...")
yolo = YOLO(MODEL_PATH)
print("✅ YOLO loaded successfully")

# latest YOLO results per zone (for dashboard)
yolo_cache = {}

# =========================
# IMAGE + DETECTION
# =========================
def pick_image(zone_id: int):
    folder = BASE_IMAGE_PATH / f"zone{zone_id}"
    if not folder.exists():
        return None
    images = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
    return random.choice(images) if images else None

def detect_people(image_path: Path):
    img = cv2.imread(str(image_path))
    if img is None:
        return 0, None

    results = yolo(img, conf=0.3, verbose=False)

    people_count = 0
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0:  # person class
                people_count += 1

    annotated = results[0].plot()
    _, buf = cv2.imencode(".jpg", annotated)
    encoded = base64.b64encode(buf).decode()

    return people_count, encoded

# =========================
# RISK LOGIC
# =========================
def compute_risk(people: int, total_beds: int):
    if total_beds <= 0:
        return 150.0, "Severe"

    ratio = (people / total_beds) * 100

    if ratio >= 100:
        return ratio, "Severe"
    elif ratio >= 70:
        return ratio, "Elevated"
    elif ratio >= 40:
        return ratio, "Caution"
    else:
        return ratio, "Safe"

# =========================
# YOLO CORE LOOP
# =========================
def yolo_loop():
    print("🚀 YOLO detection loop started")

    while True:
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT * FROM Zones")
        zones = cur.fetchall()

        for zone in zones:
            zid = zone["id"]

            image = pick_image(zid)
            if not image:
                continue

            detected_people, img64 = detect_people(image)

            # -------------------------------
            # BED ALLOCATION
            # -------------------------------
            beds_to_allocate = min(detected_people, zone["available_beds"])
            remaining = beds_to_allocate

            cur.execute("""
                SELECT id, available_beds
                FROM Shelters
                WHERE zone_id=%s AND available_beds>0
                ORDER BY available_beds DESC
            """, (zid,))
            shelters = cur.fetchall()

            for s in shelters:
                if remaining <= 0:
                    break
                take = min(s["available_beds"], remaining)
                cur.execute(
                    "UPDATE Shelters SET available_beds = available_beds - %s WHERE id=%s",
                    (take, s["id"])
                )
                remaining -= take

            cur.execute("""
                SELECT SUM(available_beds) AS beds
                FROM Shelters WHERE zone_id=%s
            """, (zid,))
            available_beds = cur.fetchone()["beds"] or 0

            # -------------------------------
            # RISK
            # -------------------------------
            risk_score, risk_level = compute_risk(
                detected_people,
                zone["total_beds"]
            )

            # -------------------------------
            # UPDATE ZONE
            # -------------------------------
            cur.execute("""
                UPDATE Zones SET
                    detected_people=%s,
                    available_beds=%s,
                    risk_score=%s,
                    risk_level=%s
                WHERE id=%s
            """, (
                detected_people,
                available_beds,
                risk_score,
                risk_level,
                zid
            ))

            # -------------------------------
            # VOLUNTEER LOGIC (FIXED)
            # 1 volunteer per 10 people
            # -------------------------------
            volunteers_needed = max(1, math.ceil(detected_people / 5))

            cur.execute("""
                INSERT INTO Assignments
                (zone_id, volunteers_assigned, beds_allocated)
                VALUES (%s,%s,%s)
            """, (zid, volunteers_needed, beds_to_allocate))

            # -------------------------------
            # ALERTS
            # -------------------------------
            if risk_level != "Safe":
                cur.execute("""
                    INSERT INTO Alerts(zone_id, level, message)
                    VALUES (%s,%s,%s)
                """, (
                    zid,
                    risk_level,
                    f"{risk_level} risk detected in {zone['name']}"
                ))

            # -------------------------------
            # YOLO CACHE (FRONTEND)
            # -------------------------------
            yolo_cache[zid] = {
                "zone_id": zid,
                "zone_name": zone["name"],
                "people_detected": detected_people,
                "image": img64,
                "timestamp": time.time()
            }

        cur.close()
        conn.close()
        time.sleep(PROCESS_INTERVAL)

# =========================
# API ENDPOINTS
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
        SELECT * FROM Assignments
        WHERE zone_id=%s
        ORDER BY created_at DESC
        LIMIT 30
    """, (zone_id,))
    history = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "zone": zone,
        "history": history
    }

@app.get("/api/alerts")
def get_alerts():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, z.name AS zone_name
        FROM Alerts a
        JOIN Zones z ON z.id=a.zone_id
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

# =========================
# STARTUP
# =========================
@app.on_event("startup")
def startup():
    threading.Thread(target=yolo_loop, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
