import cv2


def get_frame():
    """Captura un frame de la cámara"""
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    cam.release()
    if not ret:
        raise RuntimeError("No se pudo acceder a la cámara")
    return frame


def get_camera_stream():
    """Retorna el objeto de cámara para streaming continuo"""
    return cv2.VideoCapture(0)




























