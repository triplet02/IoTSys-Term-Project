import RPi.GPIO as GPIO
from socket import *
from select import *

LIVING_ROOM = 17
BATH_ROOM = 27
INNER_ROOM = 22

LIVING_ROOM_ON = '17100'
LIVING_ROOM_OFF = '17101'
BATH_ROOM_ON = '27100'
BATH_ROOM_OFF = '27101'
INNER_ROOM_ON = '22100'
INNER_ROOM_OFF = '22101'

GPIO.setmode(GPIO.BCM)
GPIO.setup(LIVING_ROOM, GPIO.OUT)
GPIO.setup(BATH_ROOM, GPIO.OUT)
GPIO.setup(INNER_ROOM, GPIO.OUT)
GPIO.setwarnings(False)

HOST = '192.168.137.175'
PORT = 10000
BUF_SIZE = 512
ADDR = (HOST, PORT)

server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(ADDR)
print('bind')

server_socket.listen(1)
print('listen')

client_socket, addr_info = server_socket.accept()
print('accept')


while True:
	data = client_socket.recv(65535).decode()
	print(data)
	
	if data == LIVING_ROOM_ON:
		GPIO.output(LIVING_ROOM, True)
	elif data == LIVING_ROOM_OFF:
		GPIO.output(LIVING_ROOM, False)
	elif data == BATH_ROOM_ON:
		GPIO.output(BATH_ROOM, True)
	elif data == BATH_ROOM_OFF:
		GPIO.output(BATH_ROOM, False)
	elif data == INNER_ROOM_ON:
		GPIO.output(INNER_ROOM, True)
	elif data == INNER_ROOM_OFF:
		GPIO.output(INNER_ROOM, False)
	else:
		print("Unsupported Command : {0}".format(data))

