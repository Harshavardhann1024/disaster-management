from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from datetime import datetime

# -------------------- APP --------------------
app = FastAPI(title="EcoRescue Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- DB --------------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Harsha@2426",
        database="ecorescue"
    )

# -------------------- YOLO DETECTION INGEST --------------------
@app.post("/detect")
def detect_people(zone_id: int, people_detected: int):
    """
    Called after YOLO detects people in a zone
    """

    db = get_db()
    cursor = db.cursor()

    # 1️⃣ Insert detection event
    cursor.execute("""
        INSERT INTO Detections (zone_id, detected_people, detection_time)
        VALUES (%s, %s, %s)
    """, (zone_id, people_detected, datetime.now()))

    # 2️⃣ Reduce available beds (EVENT BASED)
    cursor.execute("""
        UPDATE Shelters
        SET available_beds = GREATEST(0, available_beds - %s)
        WHERE zone_id = %s
    """, (people_detected, zone_id))

    # 3️⃣ Update zone risk & color
    cursor.execute("""
        UPDATE Zones z
        JOIN (
            SELECT 
                d.zone_id,
                SUM(d.detected_people) AS total_people,
                SUM(s.available_beds) AS beds
            FROM Detections d
            JOIN Shelters s ON d.zone_id = s.zone_id
            GROUP BY d.zone_id
        ) x ON z.id = x.zone_id
        SET 
            z.risk_level = CASE
                WHEN x.total_people > x.beds THEN 'Severe'
                WHEN x.total_people > x.beds * 0.7 THEN 'Elevated'
                WHEN x.total_people > x.beds * 0.4 THEN 'Caution'
                ELSE 'Safe'
            END,
            z.color = CASE
                WHEN x.total_people > x.beds THEN 'red'
                WHEN x.total_people > x.beds * 0.7 THEN 'orange'
                WHEN x.total_people > x.beds * 0.4 THEN 'yellow'
                ELSE 'green'
            END,
            z.last_update = NOW()
    """)

    # 4️⃣ Auto assign volunteers
    cursor.execute("""
        UPDATE Volunteers v
        JOIN Zones z ON v.zone_id = z.id
        SET v.status = 'Assigned'
        WHERE z.risk_level IN ('Elevated', 'Severe')
        AND v.status = 'Available'
        LIMIT 3
    """)

    db.commit()
    db.close()

    return {"status": "Detection processed"}

# -------------------- DASHBOARD --------------------
@app.get("/dashboard")
def dashboard():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Zones
    cursor.execute("""
        SELECT
            z.id AS zone_id,
            z.name,
            IFNULL(SUM(d.detected_people), 0) AS people_detected,
            SUM(s.available_beds) AS available_beds,
            z.risk_level,
            z.color
        FROM Zones z
        LEFT JOIN Detections d ON z.id = d.zone_id
        LEFT JOIN Shelters s ON z.id = s.zone_id
        GROUP BY z.id
    """)
    zones = cursor.fetchall()

    # Volunteers
    cursor.execute("""
        SELECT COUNT(*) AS active
        FROM Volunteers
        WHERE status = 'Assigned'
    """)
    volunteers = cursor.fetchone()["active"]

    # Critical zones
    cursor.execute("""
        SELECT COUNT(*) AS critical
        FROM Zones
        WHERE risk_level IN ('Elevated', 'Severe')
    """)
    critical = cursor.fetchone()["critical"]

    db.close()

    return {
        "zones": zones,
        "active_volunteers": volunteers,
        "critical_zones": critical
    }

# -------------------- RESET (FOR DEMO) --------------------
@app.post("/reset")
def reset_system():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM Detections")
    cursor.execute("UPDATE Shelters SET available_beds = total_beds")
    cursor.execute("""
        UPDATE Zones
        SET risk_level='Safe', color='green'
    """)
    cursor.execute("""
        UPDATE Volunteers
        SET status='Available'
    """)

    db.commit()
    db.close()

    return {"status": "System reset completed"}
