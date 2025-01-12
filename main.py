from threading import Thread
from time import sleep
import cv2
import easyocr
import google.generativeai as genai
import numpy as np
from braille import text_to_braille
from PIL import Image, ImageEnhance

# Shutdown flag
shutdown = [False]

# Data from OCR each element is a tuple containing bboxes, text, and confidence
current_data = []

# Delay for prompt generation
delay = 10

# Google API
genai.configure(api_key="AIzaSyBxe8-1uCdbharfPs-o8f0b0yKMX03i1MA")
model = genai.GenerativeModel("gemini-1.5-flash")

# OCR
reader = easyocr.Reader(['en'], gpu=True)

# Capturing camera input
camera = cv2.VideoCapture(0)

# Get phrases from data
def get_phrases(data):
    phrases = []
    for d in data:
        phrases.append(d[1])
    return phrases

# Receives one data element and decides whether it should be added to the current data
def decide(data):
    bbox, text, conf = data

    # Confidence
    if conf > 0.9:
        text = text.lower()

        if text not in get_phrases(current_data):
            current_data.append((bbox, text, conf))

# Prompt generation, ran in a separate thread
def prompt_gemini(shutdown):
    while not shutdown[0]:        
        phrases = get_phrases(current_data)

        # Only generate prompt if there are phrases
        if len(get_phrases(current_data)) > 0:
            text = "\"" + "\", \"".join(phrases) + "\""

            # Read pre-determined prompt from prompt.txt
            file = open("prompt.txt", 'r')
            prompt = file.read()

            # Appends the phrases to the end of the prompt, 
            # the phrase is designed to let the model know that this is the input
            prompt += text

            file.close()

            print("Words read:", text)
            response = model.generate_content(prompt)
            text = response.text
            current_data.clear()

            print("Words output:", text)

            # Model outputs phrases separated by " | ", so we split them into an array 
            # and interate over them to convert them to braille
            phrases = text.split(" | ")
            for phrase in phrases:
                phrase = phrase.replace("\n", "")

                if phrase == "":
                    continue

                braille = text_to_braille(phrase)
                print("From:", phrase, "to:", braille)

        sleep(delay)

# Processes camera input using easyocr, ran in a separate thread
def camera_stream_process(shutdown):
    count = 0
    while not shutdown[0]:
        ret, frame = camera.read()
        if not ret:
            shutdown[0] = True
            break
        
        frame = cv2. cvtColor(frame, cv2. COLOR_BGR2GRAY)

        enhancer = ImageEnhance.Contrast(Image.fromarray(frame))
        frame = enhancer.enhance(1.5)
        frame = np.array(frame)

        cv2.imshow("Camera", frame)

        if count % 60 == 0:
            data = reader.readtext(frame)

            for d in data:
                decide(d)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            shutdown[0] = True
            break

        count += 1
    
    camera.release()
    cv2.destroyAllWindows()

# creating and starting threads so that both processes can run simultaneously
gemini_thread = Thread(target=prompt_gemini, args=(shutdown,))      
ocr_thread = Thread(target=camera_stream_process, args=(shutdown,))

gemini_thread.start()
ocr_thread.start()

