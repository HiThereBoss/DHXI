import cv2
import matplotlib.pyplot as plt
import easyocr

reader = easyocr.Reader(['en'], gpu=True)

camera = cv2.VideoCapture(1)

count = 0
while True:
    ret, frame = camera.read()
    if not ret:
        break

    cv2.imshow("Camera", frame)

    if count % 60 == 0:
        data = reader.readtext(frame)
        for d in data:
            bbox, text, conf = d
            if conf > 0.8:
                print(text)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    count += 1

camera.release()
cv2.destroyAllWindows()