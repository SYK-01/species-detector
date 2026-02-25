from ultralytics import YOLO
import cv2

# Cargar modelo una sola vez
_model = None


def get_model():
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")
    return _model


def detect_species(frame):
    """Detecta especies en un frame y retorna lista de resultados"""
    model = get_model()
    results = model(frame)
    detections = []

    for r in results:
        for box in r.boxes:
            name = model.names[int(box.cls[0])]
            confidence = float(box.conf[0])
            detections.append({
                'class': name,
                'confidence': confidence,
                'confidence_pct': f"{confidence * 100:.1f}%",
            })

    # Ordenar por confianza descendente
    detections.sort(key=lambda x: x['confidence'], reverse=True)
    return detections













