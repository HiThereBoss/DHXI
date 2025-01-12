from threading import Thread
from time import sleep
import cv2
import easyocr
import pickle
import socket
import select
import google.generativeai as genai
import numpy as np
from braille import text_to_braille
from PIL import Image, ImageEnhance

HEADER_LENGTH = 100

IP = "172.20.10.5"
PORT = 1234

client = None

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

def braille_conversion(braille_char):

    cell_to_pin = {
        (0, 0): 19,
        (1, 0): 12,
        (2, 0): 13,
        (0, 1): 18,
        (1, 1): 17,
        (2, 1): 27
    }
    #use bit masking, will help determine which pins to keep and not
    if braille_char == " ":
        return [[0, 0], [0, 0], [0, 0]]
    else:
        braille_value = ord(braille_char) - 0x2800
    
        grid = [
        [bool(braille_value & 0b000001), bool(braille_value & 0b001000)],  # Row 1: Dots 1, 4
        [bool(braille_value & 0b000010), bool(braille_value & 0b010000)],  # Row 2: Dots 2, 5
        [bool(braille_value & 0b000100), bool(braille_value & 0b100000)]   # Row 3: Dots 3, 6
    ]

    new_grid = []
    for row in grid:
        new_row = []
        for cell in row:
            new_row.append(int(cell))  # Convert each cell to an integer
        new_grid.append(new_row)  # Append the converted row to the new grid


    #the grid is ready to develop the physical braille

    data = []

    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            pin_number = cell_to_pin[(i, j)]
            data.append((pin_number, cell))
                
    if client:      
        message = {}
        message['header'] = f'{len(pickle.dumps(data)):<{HEADER_LENGTH}}'.encode('utf-8')
        message['data'] = pickle.dumps(data)
        client.send(message['header'] + message['data'])

    return new_grid

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

                for char in braille:
                    braille_conversion(char)

        sleep(delay)

# Processes camera input using easyocr, ran in a separate thread
def camera_stream_process(shutdown):
    count = 0
    while not shutdown[0]:
        ret, frame = camera.read()
        if not ret:
            shutdown[0] = True
            break
        
        frame = cv2.cvtColor(frame, cv2. COLOR_BGR2GRAY)

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


def socket_server():
    global client
    def receive_message(client_socket):
        global frame, current_image
        
        try:
            data = client_socket.recv(HEADER_LENGTH)
            current_image += data
            print(current_image)
        except:
            
            if current_image != b'':
                print(current_image)
                frame = pickle.loads(current_image)
                print("Received frame")
                current_image = b''
            return

    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((IP, PORT))

    server.listen()
    server.setblocking(False)
    sockets_list = [server]

    print(f'Listening for connections on {IP}:{PORT}...')

    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

        

        # Iterate over notified sockets
        for notified_socket in read_sockets:

            # If notified socket is a server socket - new connection, accept it
            if notified_socket == server:

                # Accept new connection
                # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                # The other returned object is ip/port set
                client_socket, client_address = server.accept()

                # Add accepted socket to select.select() list
                sockets_list.append(client_socket)
                client = client_socket

                print('Accepted new connection from {}'.format(*client_address))


            # Else existing socket is sending a message
            else:
 
                # Receive message
                # message = receive_message(notified_socket)

                # # If False, client disconnected, cleanup
                # if message is False:
                #     print('Closed connection')

                #     # Remove from list for socket.socket()
                #     sockets_list.remove(notified_socket)

                #     client = None
                #     continue
                pass
        
                

                

        # It's not really necessary to have this, but will handle some socket exceptions just in case
        for notified_socket in exception_sockets:

            # Remove from list for socket.socket()
            sockets_list.remove(notified_socket)

            client = None


socket_thread = Thread(target=socket_server)
socket_thread.start()

# creating and starting threads so that both processes can run simultaneously
gemini_thread = Thread(target=prompt_gemini, args=(shutdown,))      
ocr_thread = Thread(target=camera_stream_process, args=(shutdown,))

gemini_thread.start()
ocr_thread.start()

