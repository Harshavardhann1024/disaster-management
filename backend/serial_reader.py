import serial
import threading
import time
import mysql.connector

# =========================
# CONFIG
# =========================
# You might need to change this port to match your Arduino (e.g., COM3, COM4, /dev/ttyACM0)
SERIAL_PORT = "COM13"
BAUD_RATE = 115200

DB = {
    "host": "localhost",
    "user": "root",
    "password": "Harsha@2426",
    "database": "ecorescue",
    "autocommit": True
}

# Assuming the demo is for Zone 1 (Indira Nagar)
DEFAULT_ZONE_ID = 1

def get_db():
    return mysql.connector.connect(**DB)

def handle_medical_emergency(bpm, status, lat, lng):
    print(f"[SERIAL] Processing medical emergency: BPM={bpm}, Status={status}, Lat={lat}, Lng={lng}")
    try:
        conn = get_db()
        cur = conn.cursor()

        # Insert into MedicalEmergencies
        cur.execute("""
            INSERT INTO MedicalEmergencies (zone_id, bpm, status, latitude, longitude)
            VALUES (%s, %s, %s, %s, %s)
        """, (DEFAULT_ZONE_ID, bpm, status, lat, lng))

        # If abnormal, trigger a severe alert and decrement bed
        if status == "ABNORMAL":
            cur.execute("""
                INSERT INTO Alerts (zone_id, level, message)
                VALUES (%s, 'Severe', %s)
            """, (DEFAULT_ZONE_ID, f"Medical Emergency! Abnormal BPM ({bpm}) at Location: {lat}, {lng}"))

            # Attempt to allocate a bed in the zone
            cur.execute("""
                SELECT id, available_beds
                FROM Shelters
                WHERE zone_id=%s AND available_beds > 0
                ORDER BY available_beds DESC
                LIMIT 1
            """, (DEFAULT_ZONE_ID,))
            shelter = cur.fetchone()
            
            if shelter:
                cur.execute(
                    "UPDATE Shelters SET available_beds = available_beds - 1 WHERE id = %s",
                    (shelter[0],)
                )

                # Update Zone aggregate
                cur.execute("""
                    UPDATE Zones z
                    SET available_beds = (
                        SELECT SUM(s.available_beds)
                        FROM Shelters s
                        WHERE s.zone_id = z.id
                    )
                    WHERE z.id = %s
                """, (DEFAULT_ZONE_ID,))

        cur.close()
        conn.close()
        print(f"[SERIAL] Saved medical emergency successfully.")
    except Exception as e:
        print(f"[SERIAL] DB Error handling medical emergency: {e}")

def serial_loop():
    print(f"🚀 Serial reader started on {SERIAL_PORT}")
    ser = None
    try:
        # We wrap this in a loop so it keeps trying to connect if Arduino is unplugged
        while True:
            if ser is None or not ser.is_open:
                try:
                    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                    print(f"✅ Connected to Arduino on {SERIAL_PORT}")
                except Exception as e:
                    print(f"⚠️ Could not connect to {SERIAL_PORT}. Retrying in 5s... ({e})")
                    time.sleep(5)
                    continue

            try:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("MOTION,"):
                    # Expected format: MOTION,<BPM>,<STATUS>,<LAT>,<LNG>
                    # Example: MOTION,86,NORMAL,12.923700,77.498600
                    # Example without GPS fix: MOTION,86,NORMAL,GPS_NOT_FIXED
                    parts = line.split(",")
                    if len(parts) >= 4:
                        bpm = int(parts[1])
                        status = parts[2]
                        
                        lat = None
                        lng = None
                        if parts[3] != "GPS_NOT_FIXED" and len(parts) >= 5:
                            lat = float(parts[3])
                            lng = float(parts[4])
                        
                        handle_medical_emergency(bpm, status, lat, lng)
            except Exception as e:
                print(f"[SERIAL] Error reading from port: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"💥 Serial thread crashed: {e}")

def start_serial_reader():
    thread = threading.Thread(target=serial_loop, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    serial_loop()
