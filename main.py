from threading import Thread
from time import sleep
import cv2
import easyocr
import google.generativeai as genai
from PIL import Image, ImageEnhance
import numpy as np
from difflib import SequenceMatcher

shutdown = [False]

current_data = []

delay = 10

genai.configure(api_key="AIzaSyBxe8-1uCdbharfPs-o8f0b0yKMX03i1MA")
model = genai.GenerativeModel("gemini-1.5-flash")

reader = easyocr.Reader(['en'], gpu=True)
camera = cv2.VideoCapture(0)

def get_phrases(data):
    phrases = []
    for d in data:
        phrases.append(d[1])
    return phrases

# Receives one data element, containing bbox, text, and confidence
def decide(data):
    bbox, text, conf = data

    # Confidence
    if conf > 0.9:
        text = text.lower()
        print("Read:", text)
        if text not in get_phrases(current_data):
            current_data.append((bbox, text, conf))
            
def prompt_gemini(shutdown):
    while not shutdown[0]:
        if 0xFF == ord('q'):
            break
        
        phrases = get_phrases(current_data)

        if len(get_phrases(current_data)) > 0:
            text = "\"" + "\", \"".join(phrases) + "\""

            file = open("prompt.txt", 'r')
            prompt = file.read()

            prompt += text

            file.close()

            print("Words read:", text)
            response = model.generate_content(prompt)
            phrases.clear()

            print("Words output:", response.text)

        sleep(delay)

def camera_stream_process(shutdown):
    count = 0
    while not shutdown[0]:
        ret, frame = camera.read()
        if not ret:
            shutdown[0] = True
            break

        cv2.imshow("Camera", frame)

        if count % 60 == 0:

            new_frame = cv2. cvtColor(frame, cv2. COLOR_BGR2GRAY)

            enhancer = ImageEnhance.Contrast(Image.fromarray(frame))
            new_frame = enhancer.enhance(1.5)
            new_frame = np.array(new_frame)

            data = reader.readtext(new_frame)

            for d in data:
                decide(d)
            
            print("Current phrases:", get_phrases(current_data))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            shutdown[0] = True
            break

        count += 1
    
    camera.release()
    cv2.destroyAllWindows()


gemini_thread = Thread(target=prompt_gemini, args=(shutdown,))      
ocr_thread = Thread(target=camera_stream_process, args=(shutdown,))

gemini_thread.start()
ocr_thread.start()

