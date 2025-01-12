import socket
import pickle
import errno
import RPi.GPIO as GPIO
from time import sleep
from threading import Thread

# TODO: INSTALL OPENCV
# COMMAND: pip3 install opencv-python

IP = "172.20.10.5"
PORT = 1234

HEADER_LENGTH = 100

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP, PORT))
client.setblocking(False)

character_buffer = []

character_delay = 0.1
character_duration = 0.1
servo_pins= [19, 18, 12, 13]
LED_PINS = [17, 27]

GPIO.setmode(GPIO.BCM)
for p in LED_PINS:
    GPIO.setup(p, GPIO.OUT)

# Set up each pin as output and initialize PWM
servos = {}
for pin in servo_pins:
    GPIO.setup(pin, GPIO.OUT)
    servos[pin] = GPIO.PWM(pin, 50)  # 50Hz PWM frequency
    servos[pin].start(0)  # Start PWM with 0 duty cycle

def set_angle(servo, angle):
    """
    Function to set the angle of a servo motor.
    :param servo: PWM object for the servo
    :param angle: Desired angle (0 to 180 degrees)
    """
    duty = 2 + (angle / 18)  # Convert angle to duty cycle
    servo.ChangeDutyCycle(duty)
    sleep(0.5)  # Allow time for the servo to reach position
    servo.ChangeDutyCycle(0)  # Stop signal to prevent jitter

def reset():
    """
    Function to reset the servos to their initial positions.
    """
    for servo in servos.values():
        set_angle(servo, 0)
        sleep(0.5)  # Allow time for the servo to reach position
    for led in LED_PINS:
        GPIO.output(led, GPIO.LOW)

def clean():
    # Clean up GPIO and stop all PWM
    for servo in servos.values():
        servo.stop()
    GPIO.cleanup()
    print("GPIO cleanup completed.")  

def angle_to_duty_cycle(angle):
    return 2.5 + (angle / 180.0) * 10

def process_characters():
    reset()
    global character_buffer

    shouldProcess = True

    while True and shouldProcess:
        shouldProcess = False

        for char_data in character_buffer:
            for pin in char_data:
                print(pin)
                pin_number, state = pin # the pin number, and the state value (0 or 1)
                if state:
                    if pin_number in LED_PINS:
                        GPIO.output(pin_number, GPIO.HIGH)
                    else:
                        set_angle(servos[pin_number], 90)
            character_buffer.remove(char_data)

        # 
        sleep(character_delay)
        reset()
        shouldProcess = True

def startBackground():
    frame_count = 0
    while True:
        try:
            # Now we want to loop over received messages (there might be more than one) and print them
        
            # Receive our "header" containing message length, it's size is defined and constant
            header = client.recv(HEADER_LENGTH)

            # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(header):
                print('Connection closed by the server')
                break

            # Convert header to int value
            message_length = int(header.decode('utf-8').strip())

            # Receive and decode message
            message = client.recv(message_length)

            # Depickle the message into its rightful data type
            data = pickle.loads(message) # of the form [(pin_number, cell), ...], 6 elements representing all 6 pins

            print(f"Received message: {data}")
            # Append the data to the character buffer
            character_buffer.append(data)


        except IOError as e:
            # This is normal on non blocking connections - when there are no incoming data error is going to be raised
            # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
            # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
            # If we got different error code - something happened
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))


background = Thread(target=startBackground)
background.start()

process = Thread(target=process_characters)
process.start()