import socket
import threading
from twilio_wrap import twilio_sender
import thingspeak_wrap as ts
from dust_sensor import sensor
import pigpio
import RPi.GPIO as GPIO
from datetime import datetime
import time
import sys

HOST = '192.168.137.164'
PORT = 10000

ON = '100'
OFF = '101'
STATUS = '110'
AUTO = '111'

ONOFF_CH = 1
RUNTIME_CH = 2
PM_CH = 3
ON_VAL = 1
OFF_VAL = 0

sockfd = socket.socket(socket.AF_INET)
sockfd.bind((HOST, PORT))
sockfd.listen(1)
client_sock, addr_info = sockfd.accept()

class AirPurifier(threading.Thread):
    
    def __init__(self):
        super(AirPurifier, self).__init__()
        self.centry_mode = False
        self.PM_count = None
        self.AP_running = False
        self.on_SMS_sent = False
        self.on_time = None
        self.off_time = None
        
    def run(self):
        # dust sensor pin setting
        pi = pigpio.pi('localhost')
        #dust_sensor = sensor(pi, 4)  #GPIO pin 4 : PM10
        dust_sensor = sensor(pi, 2)  #GPIO pin 6 : PM25

        # LED pin setting
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(21, GPIO.OUT)
        GPIO.output(21, False)

        SUSPEND = 3
        suspend_timer = 0

        while True:
            message = None
            timestamp = datetime.now()
            residual = timestamp
            timestamp = str(timestamp).split('.')[0]
            
            if self.AP_running:
                GPIO.output(21, True)
                if not self.on_SMS_sent:
                    ts.update((ONOFF_CH,),(ON_VAL,))
                    self.on_time = residual
                    message = timestamp+" >>> Air Purifier Activated."
                    twilio_sender(message)
                    self.on_SMS_sent = True
                elif self.PM_count is not None:
                    ts.update((ONOFF_CH, PM_CH,), (ON_VAL, self.PM_count,))
                print("[Device] AIR PURIFIER -Power On.")
            else:
                GPIO.output(21, False)
                if self.on_SMS_sent:
                    message = timestamp+" >>> Air Purifier Deactivated."
                    twilio_sender(message)
                    self.off_time = residual
                    self.on_SMS_sent = False
                    ts.update((ONOFF_CH, RUNTIME_CH),(OFF_VAL, (self.off_time-self.on_time).seconds))
                elif self.PM_count is not None:
                    ts.update((ONOFF_CH, PM_CH,), (OFF_VAL, self.PM_count,))
                print("[Device] AIR PURIFIER -Power Off.")
                    
            if self.centry_mode:
                print("[Device] AIR PURIFIER -Centry Mode Activated.")
                print(">>> Measuring...")
                    
            dust_sensor.measureStart()
            time.sleep(30)
            dust_sensor.measureStop()
                
            gpio, interval, ratio, self.PM_count, total_interrupt_count, wrong_level_count = dust_sensor.read()
                
            # If PM_count is less than Zero (Negative Value) set PM10 Count to Zero
            # If PM_count gets error value set to zero.
            if self.PM_count < 0 or self.PM_count == 1114000.62:    
                self.PM_count = 0
                
            if self.centry_mode:
                print("--")
                print("Time: {}, Interval: {}, Ratio: {:.3f}, Count: {}, Total Interrupt: {}, Wrong Interrupt: {}". 
                    format(timestamp, int(interval), ratio, int(self.PM_count), total_interrupt_count, wrong_level_count))
                
                if self.PM_count > 1000:  #threshold
                    if not self.AP_running:
                        self.AP_running = True
                        GPIO.output(21, True)
                        if not self.on_SMS_sent:
                            ts.update((ONOFF_CH, PM_CH),(ON_VAL, self.PM_count))
                            self.on_time = residual
                            message = timestamp+" >>> Air Purifier Activated."
                            twilio_sender(message)
                            print("\t>>> Message Sent : ", message, '\n')
                            self.on_SMS_sent = True
                    else:
                        ts.update((ONOFF_CH, PM_CH,), (ON_VAL, self.PM_count,))
                        suspend_timer = 0
                        print("\t( Air Purifier is RUNNING. )\n")
                
                else:
                    if self.AP_running:
                        suspend_timer += 1
                        if suspend_timer > SUSPEND:
                            self.AP_running = False
                            GPIO.output(21, False)
                            if self.on_SMS_sent:
                                self.off_time = residual
                                message = timestamp+" >>> Air Purifier Deactivated."
                                twilio_sender(message)
                                print("\t>>> Message Sent : ", message, '\n')
                                self.on_SMS_sent = False
                                ts.update((ONOFF_CH, RUNTIME_CH),(OFF_VAL, (self.off_time-self.on_time).seconds))
                            print("\t>>> RUNNING TIME : ", (self.off_time-self.on_time).seconds, "(sec)")
                            suspend_timer = 0
                        else:
                            ts.update((ONOFF_CH, PM_CH,), (ON_VAL, self.PM_count,))
                            print("\t( Air Purifier is RUNNING. )\n")
                    else:
                        ts.update((ONOFF_CH, PM_CH,), (OFF_VAL, self.PM_count,))
                        print("\t( Air Purifier is OFF. )\n")
        
            else:
                print("[Device] AIR PURIFIER -Centry Mode Deactivated.")
        pi.stop()


air_purifier = AirPurifier()
air_purifier.start()

while True:
    command = client_sock.recv(65535).decode()
    command = input("AP command : (ON 100 / OFF 101 / STATUS 110 / AUTO 111)")

    if command == ON: #LED
        client_sock.send("ACK".encode())
        air_purifier.AP_running = True
    elif command == OFF: #LED
        client_sock.send("ACK".encode())
        air_purifier.AP_running = False
        air_purifier.centry_mode = False
    elif command == STATUS: #dust value
        client_sock.send(str(air_purifier.PM_count).encode())
        print("Current Dust Status : ", air_purifier.PM_count)
    elif command == AUTO: #
        client_sock.send("ACK".encode())
        air_purifier.centry_mode = True
    else:
        client_sock.send("NACK".encode())
        print("Unsupported Command : ", command)
