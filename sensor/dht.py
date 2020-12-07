import sys
import adafruit_dht
import board
import time

class sensor:
    def __init__(self):
        self.ACTIVE_UPLOAD_INTERVAL = 2000 #ms        
        self.dht = None

    def initSensor(self, pin):
        self.dht = adafruit_dht.DHT22(pin, use_pulseio=False)
        return True
    
    def closeSensor(self):
        return True
    def getSensor(self):
        isSuccess = False
        temperature = 0.0
        humidity = 0.0

        try:
            temperature = self.dht.temperature
            humidity = self.dht.humidity                
            isSuccess = True
        except RuntimeError:            
            pass

        return temperature, humidity, isSuccess


# ---------------------------------------------------------------
if __name__ == "__main__":
    sensor = sensor()
    if not sensor.initSensor(board.D18):
        sys.exit(-1)

    main_is_run = True
    Debug = True
    # loop
    try:
        next_reading = round(time.time()*1000)
        while main_is_run:
            # Read sensor        
            tem, hum, ok = sensor.getSensor()
            if not ok:
                if Debug: print('Error read sensor')
            else:
                print('Temp:{} *C   Humi:{} %'.format(tem, hum)) 
            
            # Sleep to read sensor        
            next_reading += sensor.ACTIVE_UPLOAD_INTERVAL
            sleep_time = next_reading - round(time.time()*1000)
            if sleep_time > 0:
                time.sleep(sleep_time/1000.0)

    except KeyboardInterrupt:
        main_is_run = False

    sensor.closeSensor()
    del sensor
