from time import sleep
from braille import text_to_braille
import socket
import select
import pickle
from threading import Thread

HEADER_LENGTH = 100

IP = "172.20.10.5"
PORT = 1234

frame = None

client = None

current_image = b''

def get_current_frame():
    return frame

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

    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            pin_number = cell_to_pin[(i, j)]
            if client:
                data = pickle.dumps((pin_number, cell))
                message = {}
                message['header'] = f'{len(data):<{HEADER_LENGTH}}'.encode('utf-8')
                message['data'] = data
                client.sendall(message['header'] + message['data'])


    return new_grid

def test_braille_to_grid():
    # Test Braille characters
    braille_word = "⠓⠊"  # Braille for "hi"
    for braille_char in braille_word:
        print(f"Braille character: {braille_char}")
        grid = braille_conversion(braille_char)
        print("Grid representation:")
        for row in grid:
            print(row)
        print("-" * 20)

def socket_server():
    global frame, client
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

# Run the test
test_braille_to_grid()
    
