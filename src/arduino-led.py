import cv2
import requests
from ultralytics import YOLO

# --- CONFIGURAÇÃO DO ESP8266 ---
ESP_IP = "172.20.10.3"  # <- troque pelo IP do seu ESP
ESP_URL = f"http://{ESP_IP}/receber"

model = YOLO('grb-model-n.pt')
cap = cv2.VideoCapture(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow('Webcam', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Webcam', 800, 600)

ultimo_enviado = -1

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, stream=True, imgsz=480, conf=0.5)
    frame_anotado = frame

    for r in results:
        frame_anotado = r.plot()

        if len(r.boxes) > 0:
            classe_detectada = int(r.boxes.cls[0])

            if classe_detectada != ultimo_enviado:
                try:
                    requests.get(f"{ESP_URL}?classe={classe_detectada}")
                    ultimo_enviado = classe_detectada
                    print(f"Enviado via WiFi: Classe {classe_detectada}")
                except Exception as e:
                    print(f"Erro ao enviar: {e}")

    cv2.imshow('Webcam', frame_anotado)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()