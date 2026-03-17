import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import cv2
import requests
import numpy as np
from ultralytics import YOLO

# --- CONFIGURAÇÃO DO ESP32 ---
ESP_IP = "10.124.61.153"
ESP_URL = f"http://{ESP_IP}/classe"
STREAM_URL = f"http://{ESP_IP}/stream"

# carregar modelo YOLO
model = YOLO("best.pt")
model.to("cpu")

classes = {
    0: "metal",
    1: "papel",
    2: "plastico",
    3: "biologico"
}

ultimo_enviado = -1

print("Conectando ao stream...")

stream = requests.get(STREAM_URL, stream=True)

buffer = b""

for chunk in stream.iter_content(chunk_size=1024):
    buffer += chunk

    a = buffer.find(b'\xff\xd8')
    b = buffer.find(b'\xff\xd9')

    if a != -1 and b != -1:
        jpg = buffer[a:b+2]
        buffer = buffer[b+2:]

        frame = cv2.imdecode(
            np.frombuffer(jpg, dtype=np.uint8),
            cv2.IMREAD_COLOR
        )

        if frame is None:
            continue

        # --- YOLO ---
        results = model(frame, conf=0.5)

        for r in results:
            for box in r.boxes:
                classe = int(box.cls[0])
                confianca = float(box.conf[0])

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                nome = classes.get(classe, "desconhecido")

                texto = f"{nome} {confianca:.2f}"

                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                cv2.putText(frame, texto, (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0,255,0), 2)

                # envia classe para o ESP
                if classe != ultimo_enviado:
                    try:
                        response = requests.get(f"{ESP_URL}?valor={classe}", timeout=2)

                        if response.status_code == 200:
                            print(f"Enviado: {nome}")
                            ultimo_enviado = classe
                        else:
                            print("Erro no response do ESP")

                    except Exception as e:
                        print(f"Erro enviando: {e}")

        cv2.imshow("Detectado", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()