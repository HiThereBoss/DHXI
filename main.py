from threading import Thread
from time import sleep
import cv2
import easyocr
import google.generativeai as genai
from difflib import SequenceMatcher

shutdown = [False]

curr_phrases = []

delay = 10

genai.configure(api_key="AIzaSyBxe8-1uCdbharfPs-o8f0b0yKMX03i1MA")
model = genai.GenerativeModel("gemini-1.5-flash")

reader = easyocr.Reader(['en'], gpu=True)
camera = cv2.VideoCapture(0)

def string_similarity(string1, string2):
    matcher = SequenceMatcher(None, string1, string2)
    return matcher.ratio()  # Convert to percentage

# def fix_data():
#     global curr_phrases
#     data = list(dict.fromkeys(curr_phrases))

#     temp_data = data.copy()
#     for i in range(len(data)-1):
#         phrase = data[i]
#         for j in range(i+1, len(data)):
#             other_phrase = data[j]
#             if string_similarity(phrase, other_phrase) > 0.9:
#                 if len(phrase) > len(other_phrase):
#                     temp_data.remove(other_phrase)
#                 else:
#                     temp_data.remove(phrase)
#     curr_phrases = temp_data

def decide(data):
    bbox, text, conf = data

    # Confidence
    if conf > 0.9:
        text = text.lower()
        print("Read:", text)
        if text not in curr_phrases:
            for phrase in curr_phrases:
                if string_similarity(phrase, text) > 0.6:
                    curr_phrases.remove(phrase)
            
            
            curr_phrases.append(text)
            
                

# def prompt_gemini(shutdown):
#     while not shutdown[0]:
#         if 0xFF == ord('q'):
#             break

#         if len(curr_phrases) > 0:
#             text = "\"" + "\", \"".join(curr_phrases) + "\""

#             file = open("prompt.txt", 'r')
#             prompt = file.read()

#             prompt += text

#             file.close()

#             print("Words read:", text)
#             response = model.generate_content(prompt)
#             curr_phrases.clear()

#             print("Words output:", response.text)

#         sleep(delay)

def camera_stream_process(shutdown):
    count = 0
    while not shutdown[0]:
        ret, frame = camera.read()
        if not ret:
            shutdown[0] = True
            break

        cv2.imshow("Camera", frame)

        if count % 60 == 0:
            data = reader.readtext(frame)
            for d in data:
                decide(d)
            
            # fix_data()
            print("Current phrases:", curr_phrases)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            shutdown[0] = True
            break

        count += 1
    
    camera.release()
    cv2.destroyAllWindows()


# gemini_thread = Thread(target=prompt_gemini, args=(shutdown,))      
ocr_thread = Thread(target=camera_stream_process, args=(shutdown,))

# gemini_thread.start()
ocr_thread.start()

