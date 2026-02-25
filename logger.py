import json
import os
from datetime import datetime


LOG_FILE = "detections_log.json"


def save_log(detections: list):
    """Guarda las detecciones en un archivo JSON local"""
    logs = load_logs()

    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "detections": detections,
    }
    logs.append(entry)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f"✅ Log guardado: {len(detections)} detecciones")


def load_logs() -> list:
    """Carga el historial de logs"""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def print_last_log():
    """Imprime la última detección guardada"""
    logs = load_logs()
    if not logs:
        print("Sin logs aún.")
        return
    last = logs[-1]
    print(f"\n📋 Última detección: {last['timestamp']}")
    for d in last['detections']:
        print(f"   🌿 {d['class']} — {d['confidence_pct']}")












