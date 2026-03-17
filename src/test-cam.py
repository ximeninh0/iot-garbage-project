import cv2
import requests
import numpy as np

url = "http://10.124.61.153/stream"

stream = requests.get(url, stream=True)

buffer = b""

for chunk in stream.iter_content(1024):
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

        cv2.imshow("ESP32", frame)

        if cv2.waitKey(1) == 27:
            break