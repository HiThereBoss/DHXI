from threading import Thread
from time import sleep
import cv2
import easyocr
import google.generativeai as genai

shutdown = [False]

curr_phrases = []

delay = 10

genai.configure(api_key="AIzaSyBxe8-1uCdbharfPs-o8f0b0yKMX03i1MA")
model = genai.GenerativeModel("gemini-1.5-flash")

reader = easyocr.Reader(['en'], gpu=True)
camera = cv2.VideoCapture(0)

def decide(data):
    bbox, text, conf = data

    # Confidence
    if conf > 0.9:
        text = text.lower()
        
        words = text.split(' ')

        replaced = False
        for i in range(len(curr_phrases)):
            phrase = curr_phrases[i]

            count = 0
            old_words = phrase.split(' ')

            for old_word in old_words:
                if old_word in words:
                    count += 1
            
            if count / len(old_words) > 0.5:
                replaced = True
                curr_phrases.pop(i)
                curr_phrases.append(text)
        
        if not replaced:
            if text not in curr_phrases:
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

