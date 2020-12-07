# datasheet: https://www.winsen-sensor.com/d/files/ZE25-O3.pdf

import sys
import serial
import time

class sensor:
    def __init__(self):
        self.ACTIVE_UPLOAD_MODE_COMMAND = bytes.fromhex('FF 01 78 40 00 00 00 00 47')
        self.QA_MODE_COMMAND = bytes.fromhex('FF 01 78 41 00 00 00 00 46')
        self.REQUEST_COMMAND = bytes.fromhex('FF 01 86 00 00 00 00 00 79')
        self.ACTIVE_UPLOAD_MODE_TYPE = 0
        self.QA_MODE_TYPE = 1
        self.GAS_TYPE = 0x2A
        self.CONVERSION_FACTOR_N = 2.143 #O3/22.4
        self.ACTIVE_UPLOAD_INTERVAL = 1000 #ms
        self.SENSOR_SERIAL_BAUD = 9600

        self.ser = None
        self.mode = self.ACTIVE_UPLOAD_MODE_TYPE

    # Private Function
    def _checkCheckSum(self, bytesInput):
        listInput = list(bytesInput)
        length = len(listInput)
        cs = 0
        for i in range(1, length -1):
            cs = cs + listInput[i]    
        cs = 256 + (~(cs & 0xFF)) + 1
        csinput = listInput[length -1]
        return (cs == csinput)

    def _validatePacket(self, bytesInput):    
        if self.mode == self.ACTIVE_UPLOAD_MODE_TYPE:
            if len(bytesInput) != 9:
                return False
            if bytesInput[0] != 0xFF or bytesInput[1] != self.GAS_TYPE:
                return False
            return self._checkCheckSum(bytesInput)
        else:
            if len(bytesInput) != 9:
                return False
            if bytesInput[1] != 0x86:
                return False
            return self._checkCheckSum(bytesInput)
        

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
            
        if not self._validatePacket(rec_buff):
            return '', False
        return rec_buff, True

    def _caculatorGasValue(self, highByte, lowByte):    
        ppb = (highByte & 0xFF) << 8 | (lowByte & 0xFF)
        return round(self.CONVERSION_FACTOR_N*ppb, 1)

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
            return self._caculatorGasValue(packet[4], packet[5]), True        
        else:
            if self.ser.write(self.REQUEST_COMMAND) < 0:
                return 0, False
            packet, ok = self._readPacket(timeout)
            if not ok:
                return 0, False
            return self._caculatorGasValue(packet[6], packet[7]), True

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
                print('Gas:{} ug/m3'.format(gas))      
            
            # Sleep to read sensor        
            next_reading += sensor.ACTIVE_UPLOAD_INTERVAL
            sleep_time = next_reading - round(time.time()*1000)
            if sleep_time > 0:
                time.sleep(sleep_time/1000.0)

    except KeyboardInterrupt:
        main_is_run = False

    sensor.closeSensor()
    del sensor