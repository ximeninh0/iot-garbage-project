import cv2
from ultralytics import YOLO

model = YOLO('grb-model-n.pt')

cap = cv2.VideoCapture(0)

# --- 1. TRAVANDO A RESOLUÇÃO DA CÂMERA ---
# Define a resolução de captura (ex: 640x480)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# --- 2. TRAVANDO O TAMANHO DA JANELA ---
# Cria a janela permitindo redimensionamento manual/via código
cv2.namedWindow('Webcam', cv2.WINDOW_NORMAL)
# Trava o tamanho exato da janela na tela do seu notebook (ex: 800x600)
cv2.resizeWindow('Webcam', 800, 600)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Sua inferência (mantive a otimizada!)
    results = model(frame, stream=True, imgsz=480, conf=0.5) 
    
    for r in results:
        frame_anotado = r.plot() 
        
    # A imagem será exibida dentro da janela 'Webcam' de 800x600 que travamos ali em cima
    cv2.imshow('Webcam', frame_anotado)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()