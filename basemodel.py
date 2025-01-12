import cv2
import easyocr
from braille import text_to_braille
reader = easyocr.Reader(['en'], gpu=True)

camera = cv2.VideoCapture(0)

current_phrases = []

count = 0
while True:
    ret, frame = camera.read()
    if not ret:
        break

    cv2.imshow("Camera", frame)

    if count % 120 == 0:
        data = reader.readtext(frame)
        for d in data:
            bbox, text, conf = d
            print(conf)
            if conf > 0.4:
                braille_word = text_to_braille(text)
                print(braille_word) # need to communicate the braile to the raspberry pi here

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    count += 1

camera.release()
cv2.destroyAllWindows()