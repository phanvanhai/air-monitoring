# datasheet: https://docs.rs-online.com/2ecd/A700000007095397.pdf

import sys
import serial
import time

class sensor:
    def __init__(self):
        self.ACTIVE_UPLOAD_MODE_COMMAND = b'K 1\r\n'
        self.QA_MODE_COMMAND = b'K 2\r\n'
        self.REQUEST_COMMAND = b'Z\r\n'
        self.ACTIVE_UPLOAD_MODE_TYPE = 0
        self.QA_MODE_TYPE = 1
        self.CONVERSION_FACTOR_N = 10*1.964
        self.ACTIVE_UPLOAD_INTERVAL = 500 #ms        
        self.SENSOR_SERIAL_BAUD = 9600

        self.mode = self.ACTIVE_UPLOAD_MODE_TYPE
        self.ser = None
    
    # Private Function
    def _readPacket(self, timeout = 2, step_check = 0.015):
        if self.mode == self.ACTIVE_UPLOAD_MODE_TYPE and self.ser.inWaiting():
            time.sleep(step_check)
        self.ser.flushInput()
        
        rec_buff = ''
        i = 0
        while i < timeout/step_check:
            time.sleep(step_check)
            if self.ser.inWaiting():         
                time.sleep(step_check)
                rec_buff = self.ser.read(self.ser.inWaiting())
                break
            i += 1
            
        if rec_buff == '':
            return '', False    
        return rec_buff, True

    def _caculatorGasValue(self, inputAscii):
        inputStr = ''
        inputStr = inputAscii.decode()
        dataList = inputStr.split(' ')
        if len(dataList) < 3:
            return 0, False
        
        ppm = 0
        try:
            ppm = int(dataList[2])
        except:
            return 0, False

        return round(self.CONVERSION_FACTOR_N*ppm, 1), True

    # Public Function
    def initSensor(self, port, run_mode):       
        if run_mode == self.ACTIVE_UPLOAD_MODE_TYPE:
            self.mode = self.ACTIVE_UPLOAD_MODE_TYPE
        else:
            self.mode = self.QA_MODE_TYPE

        try:
            self.ser = serial.Serial(
                port = port,
                baudrate = self.SENSOR_SERIAL_BAUD,
                parity = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_ONE,
                bytesize = serial.EIGHTBITS,
                timeout = 10
            )
            self.ser.flushInput()
            if self.mode == self.ACTIVE_UPLOAD_MODE_TYPE:
                if self.ser.write(self.ACTIVE_UPLOAD_MODE_COMMAND) < 0:
                    return False
            else:
                if self.ser.write(self.QA_MODE_COMMAND) < 0:
                    return False
                # Flush data from ACTIVE_UPLOAD_MODE
                time.sleep(0.2)
                self.ser.flushInput()
            return True
        except serial.SerialException as e:
            print(e)
            return False

    def closeSensor(self):
        if self.ser != None:
            self.ser.close()

    def getSensor(self, timeout = 2):
        if self.mode == self.ACTIVE_UPLOAD_MODE_TYPE:
            packet, ok = self._readPacket(timeout)
            if not ok:
                return 0, False        
        else:
            if self.ser.write(self.REQUEST_COMMAND) < 0:            
                return 0, False
            packet, ok = self._readPacket(timeout)
            if not ok:
                return 0, False
        return self._caculatorGasValue(packet)


# ---------------------------------------------------------------
if __name__ == "__main__":
    sensor = sensor()
    if not sensor.initSensor('/dev/ttyUSB0', 1):
        sys.exit(-1)

    main_is_run = True
    Debug = True
    # loop
    try:
        next_reading = round(time.time()*1000)
        while main_is_run:
            # Read sensor        
            gas, ok = sensor.getSensor()
            if not ok:
                if Debug: print('Error read sensor')
            else:
                print('CO2:{} ppm'.format(gas))
            
            # Sleep to read sensor
            next_reading += sensor.ACTIVE_UPLOAD_INTERVAL
            sleep_time = next_reading - round(time.time()*1000)
            if sleep_time > 0:
                time.sleep(sleep_time/1000.0)

    except KeyboardInterrupt:
        main_is_run = False

    sensor.closeSensor()
    del sensor