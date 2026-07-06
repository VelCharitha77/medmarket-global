import csv
import os
from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = os.environ.get("SYNTHEA_DATA_DIR", "/data")

def read_csv(filename):
    """Read a Synthea CSV file and return as a list of dicts."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

@app.route("/api/patients", methods=["GET"])
def get_patients():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    patients = read_csv("patients.csv")
    page = patients[offset:offset + limit]
    return jsonify({
        "total": len(patients),
        "offset": offset,
        "limit": limit,
        "next": f"/api/patients?offset={offset + limit}&limit={limit}" if offset + limit < len(patients) else None,
        "results": page
    })

@app.route("/api/encounters", methods=["GET"])
def get_encounters():
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    encounters = read_csv("encounters.csv")
    page = encounters[offset:offset + limit]
    return jsonify({
        "total": len(encounters),
        "offset": offset,
        "limit": limit,
        "next": f"/api/encounters?offset={offset + limit}&limit={limit}" if offset + limit < len(encounters) else None,
        "results": page
    })

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
