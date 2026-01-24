import time, threading, random
import mysql.connector
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# =========================
# CONFIG
# =========================
INTERVAL = 5  # seconds

DB = {
    "host": "localhost",
    "user": "root",
    "password": "Harsha@2426",
    "database": "ecorescue",
    "autocommit": True
}

# =========================
# APP
# =========================
app = FastAPI(title="EcoRescue Backend (Simulation)")

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
# RISK LOGIC
# =========================
def compute_risk(people, beds):
    if beds <= 0:
        return 150.0, "Severe"

    ratio = (people / beds) * 100
    if ratio >= 100:
        return ratio, "Severe"
    elif ratio >= 70:
        return ratio, "Elevated"
    elif ratio >= 40:
        return ratio, "Caution"
    else:
        return ratio, "Safe"

# =========================
# CORE SIMULATION
# =========================
def process_zone(zone_id: int):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # Zone snapshot
    cur.execute("SELECT * FROM Zones WHERE id=%s", (zone_id,))
    zone = cur.fetchone()
    if not zone:
        cur.close()
        conn.close()
        return

    # Simulate detection
    new_people = random.randint(0, 10)
    detected_people = zone["detected_people"] + new_people

    # Allocate beds
    beds_to_allocate = min(new_people, zone["available_beds"])
    remaining = beds_to_allocate

    cur.execute("""
        SELECT id, available_beds
        FROM Shelters
        WHERE zone_id=%s AND available_beds>0
        ORDER BY available_beds DESC
    """, (zone_id,))
    shelters = cur.fetchall()

    for s in shelters:
        if remaining <= 0:
            break
        take = min(s["available_beds"], remaining)
        cur.execute("""
            UPDATE Shelters
            SET available_beds = available_beds - %s
            WHERE id=%s
        """, (take, s["id"]))
        remaining -= take

    # Recalculate beds
    cur.execute("""
        SELECT SUM(available_beds) AS beds
        FROM Shelters WHERE zone_id=%s
    """, (zone_id,))
    available_beds = cur.fetchone()["beds"] or 0

    # Risk
    risk_score, risk_level = compute_risk(detected_people, zone["total_beds"])

    # Update zone
    cur.execute("""
        UPDATE Zones
        SET detected_people=%s,
            available_beds=%s,
            risk_score=%s,
            risk_level=%s
        WHERE id=%s
    """, (detected_people, available_beds, risk_score, risk_level, zone_id))

    # History tables (for charts)
    cur.execute("""
        INSERT INTO Detections(zone_id, detected_people)
        VALUES (%s,%s)
    """, (zone_id, detected_people))

    volunteers_assigned = max(1, detected_people // 15)

    cur.execute("""
        INSERT INTO Assignments(zone_id, volunteers_assigned, beds_allocated)
        VALUES (%s,%s,%s)
    """, (zone_id, volunteers_assigned, beds_to_allocate))

    # Alerts
    if risk_level != "Safe":
        cur.execute("""
            INSERT INTO Alerts(zone_id, level, message)
            VALUES (%s,%s,%s)
        """, (zone_id, risk_level, f"{risk_level} risk in zone {zone_id}"))

    cur.close()
    conn.close()

# =========================
# SIMULATOR LOOP
# =========================
def simulator():
    print("🚀 Simulation started")
    while True:
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id FROM Zones")
            zones = [z[0] for z in cur.fetchall()]
            cur.close()
            conn.close()

            for zid in zones:
                process_zone(zid)

        except Exception as e:
            print("🔥 Simulator error:", e)

        time.sleep(INTERVAL)

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
        ORDER BY created_at ASC
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

# =========================
# STARTUP
# =========================
@app.on_event("startup")
def start():
    threading.Thread(target=simulator, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
