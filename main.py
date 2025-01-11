from threading import Thread
from time import sleep
import cv2
import matplotlib.pyplot as plt
import easyocr
import google.generativeai as genai

curr_words = []

delay = 3

genai.configure(api_key="AIzaSyBxe8-1uCdbharfPs-o8f0b0yKMX03i1MA")
model = genai.GenerativeModel("gemini-1.5-flash")

reader = easyocr.Reader(['en'], gpu=True)
camera = cv2.VideoCapture(1)

def decide(data):
    bbox, text, conf = data

    # Confidence
    if conf > 0.9:
        text = text.lower()

        if text not in curr_words:
            curr_words.append(text)

def prompt_gemini():
    while True:
        if 0xFF == ord('q'):
            break

        if len(curr_words) > 0:
            text = ", ".join(curr_words)

            file = open("prompt.txt", 'r')
            prompt = file.read()

            prompt += text

            file.close()

            print("Words read:", text)
            response = model.generate_content(prompt)
            curr_words.clear()

            print("Words output:", response.text)

        sleep(delay)

def ocr():
    count = 0
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        cv2.imshow("Camera", frame)

        if count % 60 == 0:
            data = reader.readtext(frame)
            for d in data:
                decide(d)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        count += 1
    
    camera.release()
    cv2.destroyAllWindows()


gemini_thread = Thread(target=prompt_gemini)      
ocr_thread = Thread(target=ocr)

gemini_thread.start()
ocr_thread.start()

