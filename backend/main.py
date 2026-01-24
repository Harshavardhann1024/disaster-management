import time
import threading
import random
import base64
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
# DB
# =========================
def get_db():
    return mysql.connector.connect(**DB)

# =========================
# YOLO
# =========================
print("🔄 Loading YOLO model...")
yolo = YOLO(MODEL_PATH)
print("✅ YOLO model loaded")

yolo_cache = {}

def pick_image(zone_id: int):
    folder = BASE_IMAGE_PATH / f"zone{zone_id}"
    if not folder.exists():
        return None
    images = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
    return random.choice(images) if images else None

def detect_people(image_path: Path):
    img = cv2.imread(str(image_path))
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

# =========================
# CORE YOLO LOOP
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

            # ⚠️ Risk calculation (FIXED)
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

            # 🧍 Volunteer assignment (FIXED)
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
                "people": total_people,
                "image": img64,
                "timestamp": time.time()
            }

        cur.close()
        conn.close()
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

# =========================
# STARTUP
# =========================
@app.on_event("startup")
def startup():
    threading.Thread(target=yolo_loop, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
