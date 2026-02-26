import cv2
import serial as serial
from ultralytics import YOLO

# --- CONFIGURAÇÃO DA PORTA SERIAL ---
# Substitua 'COM3' pela porta que o seu ESP8266 está conectado (Ex: 'COM5' no Windows ou '/dev/ttyUSB0' no Linux/Mac)
try:
    esp8266 = serial.Serial('COM5', 115200, timeout=1)
    print("Conexão com ESP8266 estabelecida!")
except Exception as e:
    print(f"Erro ao conectar na porta Serial: {e}")
    esp8266 = None

model = YOLO('grb-model-n.pt')

cap = cv2.VideoCapture(0)

# --- 1. TRAVANDO A RESOLUÇÃO DA CÂMERA ---
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# --- 2. TRAVANDO O TAMANHO DA JANELA ---
cv2.namedWindow('Webcam', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Webcam', 800, 600)

ultimo_enviado = -1 # Para evitar spam na porta serial

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, stream=True, imgsz=480, conf=0.5) 
    
    frame_anotado = frame # Caso não detecte nada, exibe o frame normal
    
    for r in results:
        frame_anotado = r.plot() 
        
        # Se detectou algum objeto
        if len(r.boxes) > 0:
            # Pega a classe do objeto com maior confiança (o primeiro da lista)
            classe_detectada = int(r.boxes.cls[0])
            
            # Só envia pela serial se for uma classe diferente da última enviada
            if esp8266 is not None and classe_detectada != ultimo_enviado:
                esp8266.write(str(classe_detectada).encode())
                ultimo_enviado = classe_detectada
                print(f"Enviado para o ESP8266: Classe {classe_detectada}")
        
    cv2.imshow('Webcam', frame_anotado)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
if esp8266:
    esp8266.close()
cv2.destroyAllWindows()