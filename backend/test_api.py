"""Quick API test script"""
import urllib.request
import json

endpoints = [
    ("Zones", "/api/zones"),
    ("Alerts", "/api/alerts"),
    ("Medical Alerts", "/api/medical-alerts"),
    ("YOLO Images", "/api/yolo-images"),
    ("Zone History (zone 1)", "/api/zone-history/1"),
    ("Shelters", "/api/shelters"),
]

for name, path in endpoints:
    try:
        r = urllib.request.urlopen(f"http://localhost:8000{path}")
        data = json.loads(r.read())
        if isinstance(data, list):
            print(f"  OK {name}: {len(data)} records")
        elif isinstance(data, dict):
            print(f"  OK {name}: {list(data.keys())}")
        else:
            print(f"  OK {name}: OK")
    except Exception as e:
        print(f"  FAIL {name}: {e}")

print("\nAll API tests done!")
