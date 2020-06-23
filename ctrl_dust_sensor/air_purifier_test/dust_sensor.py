
import math
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pigpio  # need to execute "sudo pigpiod" in advance

class sensor:

    def __init__(self, pi, gpio):

        self.pi = pi
        self.gpio = gpio

        self._start_tick = None
        self._last_tick = None
        self._low_ticks = 0
        self._high_ticks = 0
        self._last_level = 0

        self.wrong_level_count = 0
        self.total_interrupt_count = 0
        self.on_measure = False

        pi.set_mode(gpio, pigpio.INPUT)
        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)
    
    def measureStart(self):
        self.on_measure = True
        self._start_tick = self._last_tick = self.pi.get_current_tick()
        self._last_level = self.pi.read(self.gpio)
    
    def measureStop(self):
        self.on_measure = False

        # lastly check the level time and add
        level = self.pi.read(self.gpio)
        tick = self.pi.get_current_tick()
        ticks = pigpio.tickDiff(self._last_tick, tick)

        if level == 0: # last level to timeout is low               
            self._low_ticks += ticks
        elif level == 1: # last level to timeout is high     
            self._high_ticks += ticks
        else: # timeout level, not used
            pass

    # Method for calculating Ratio and Concentration
    def read(self):
    
        interval = self._low_ticks + self._high_ticks

        if interval > 0:
            ratio = float(self._low_ticks)/float(interval)*100.0
            concentration = 1.1*pow(ratio,3)-3.8*pow(ratio,2)+520*ratio+0.62
        else:
            ratio = 0
            concentration = 0.0
        
        tcnt = self.total_interrupt_count
        wcnt = self.wrong_level_count

        self.total_interrupt_count = 0
        self.wrong_level_count = 0

        self._start_tick = None
        self._last_tick = None
        self._low_ticks = 0
        self._high_ticks = 0
        self._last_level = 0
        
        return (self.gpio, interval, ratio, concentration, tcnt, wcnt)

    def _cbf(self, gpio, level, tick):

        if self.on_measure == False:
                return

        if self._start_tick is not None:

            ticks = pigpio.tickDiff(self._last_tick, tick)
            self._last_tick = tick
            self.total_interrupt_count += 1

            if self._last_level == level:
                self.wrong_level_count += 1
                return
            else:
                self._last_level = level

            if level == 0: # Falling edge.                
                self._high_ticks += ticks
            elif level == 1: # Rising edge.
                self._low_ticks += ticks
            else: # timeout level, not used
                pass

        else:
            self._start_tick = tick
            self._last_tick = tick
            self._last_level = level
            self.total_interrupt_count = 0
            self.wrong_level_count = 0


if __name__ == "__main__":

    from datetime import datetime
    import time
    import ds_test1 # import this script
    import sys
    
    pi = pigpio.pi('localhost')
    s10 = ds_test1.sensor(pi, 4)  #  GPIO 4 - Seosor Pin 4 (PM10)
    s25 = ds_test1.sensor(pi, 2)  #  GPIO 2 - Seosor Pin 2 (PM25)
    
    while True:
        # measure at the same time ---------------------------------------------
        s10.measureStart()
        s25.measureStart()
        time.sleep(30)  
        s10.measureStop()
        s25.measureStop()

        timestamp = datetime.now()
        g10, interval10, r10, PM10count, total_interrupt_count10, wrong_level_count10 = s10.read()
        g25, interval25, r25, PM25count, total_interrupt_count25, wrong_level_count25 = s25.read()
        

        # If PM10count is less than Zero (Negative Value) set PM10 Count to Zero
        # If PM10count gets error value set to zero.
        if PM10count < 0 or PM10count == 1114000.62:    
            PM10count = 0

        # If PM25count is less than Zero (Negative Value) set PM25 Count to Zero
        #If PM25count gets error value set to zero
        if PM25count < 0 or PM25count == 1114000.62:    
            PM25count = 0

        print("Measure at the same time --")
        print("PM1.0 time: {}, Interval: {}, Ratio: {:.3f}, Count: {}, Total Interrupt: {}, Wrong Interrupt: {}". 
            format(timestamp, int(interval10), r10, int(PM10count), total_interrupt_count10, wrong_level_count10))
        
        print("PM2.5 time: {}, Interval: {}, Ratio: {:.3f}, Count: {}, Total Interrupt: {}, Wrong Interrupt: {}". 
            format(timestamp, int(interval25), r25, int(PM25count), total_interrupt_count25, wrong_level_count25))

        print()

    pi.stop() # Disconnect from Pi.

