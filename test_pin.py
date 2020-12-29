import os
import sys
import time
import json
import requests
import argparse
import board
from datetime import datetime

from battery import INA219 as battery
from sim import sim
from sensor import zh03b
from sensor import dht

parser = argparse.ArgumentParser()
parser.add_argument('-all',     help='Use all sensor and http', action='store_true')
parser.add_argument('-dht',     help='Use DHT.      Jump Vcc-P-Gnd:1-12-9', action='store_true')
parser.add_argument('-pm25',    help='Use PM2.5.    Jump V-Tx-Rx-G:2-8-10-14', action='store_true')
parser.add_argument('-wifi',    help='Enable post data to Server via WiFi. Default = False', action='store_true')
parser.add_argument('-sim',    help='Enable post data to Server via SIM 4G. Default = False', action='store_true')
parser.add_argument('-pin',    help='Use Pin. Default = False', action='store_true')
parser.add_argument('-d', '--debug', help='enable/disable Debug. Default = False', action='store_true')
parser.add_argument('-t', '--time', help='measuring time (h). Default = 1' , type=int, default=1)
parser.add_argument('-i', '--interval', help='measuring interval time (min). Default = 1' , type=int, default=1)

option = parser.parse_args()

UseAll = option.all
UseWiFi = option.wifi or UseAll
UseSim = option.sim or UseAll
UseDHT = option.dht or UseAll
UsePM25 = option.pm25 or UseAll
UsePin = option.pin or UseAll
SensorReadMode = 1
Debug = option.debug
TimeRun = option.time
ReadSensorInterval = option.interval

folder = datetime.now().strftime("%Y%m%d%H%M") + '_' + str(TimeRun) + 'h'
if not os.path.exists(folder):
    os.mkdir(folder)

# General
# 
# Config HTTP
# URL = 'http://httpbin.org/post'
URL = 'http://45.77.243.33:8080/api/v1/iaTF9JJ7sZOsBSTEimmG/telemetry'
ContentType = 'application/json'
HTTP_CONNECT_TIMEOUT = 20   #s
HTTP_RESPONSE_TIMEOUT = 5   #s

SIM_SERIAL_PORT = '/dev/ttyUSB0'
SIM_SERIAL_BAUD = 115200
POWER_KEY = 6

# Config Sensors
PM2_5 = zh03b.sensor()
DHT = dht.sensor()

# Init Battery
Battery = None
if UsePin:
    Battery = battery.INA219(addr=0x42)

DHT_PIN = board.D18
PORT_PM2_5 = '/dev/ttyAMA0'

SENSOR_READ_INTERVAL = 1000 #ms
if UsePM25 and PM2_5.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = PM2_5.ACTIVE_UPLOAD_INTERVAL
if UseDHT and DHT.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = DHT.ACTIVE_UPLOAD_INTERVAL

# ----------------- Support funcs ------------------------
# 
def checkReadAllSensorSuccess(state):
    if UseDHT:
        if not 'dht' in state:
            return False
        if state['dht'] != True:
            return False
    if UsePM25:
        if not 'pm25' in state:
            return False
        if state['pm25'] != True:
            return False
    return True

# ----------------- HTTP funcs ------------------------
# 
def wifi_http_post(url, contentType, json_data, connTimeout, recvTimeout):
    try:
        headers={"Content-Type":contentType}        
        r = requests.post(url ,data=json_data, headers = headers,  timeout = (connTimeout, recvTimeout))
        if r.status_code == 200:
            return True
        return False       
    except requests.exceptions.RequestException as e:
        if Debug: print('WiFi: Request error:{}'.format(e))
    
    return False

def http_post(url, contentType, json_data, connTimeout, recvTimeout):
    ok = False
    if UseWiFi:
        ok = wifi_http_post(url, contentType, json_data, connTimeout, recvTimeout)
    if UseSim and not ok:
        ok = sim.http_post(url, contentType, json_data, '', connTimeout, recvTimeout)
    return ok

# ----------------- write file funcs ------------------------
# 
def writeFile(file, timeMinute, name, value, unit):
    file.write('{},{},{},{}\n'.format(timeMinute, name, value, unit))

def getTime():
    return datetime.now().strftime("%Y%m%d%H%M")

# ----------------- Main ------------------------
# 
if __name__ == "__main__":
    if UseSim:
        # init SIM
        sim.power_on(POWER_KEY)
        ok = sim.at_init(SIM_SERIAL_PORT, SIM_SERIAL_BAUD, debugMode=False)
        if not ok:
            print('SIM AT init error')
            sys.exit(1)
        
        sim.gps_start()
        # wait until GPS is ready
        print('wait until GPS is ready...')
        while True:
            time.sleep(2)
            _, ok = sim.gps_get_data()
            if ok:
                print('GPS is ready')
                break

    if UsePM25:
        ok = PM2_5.initSensor(PORT_PM2_5, SensorReadMode)
        if not ok:
            print('init PM2.5 error')
            sys.exit(-1)
    if UseDHT:
        ok = DHT.initSensor(DHT_PIN)
        if not ok:
            print('init DHT error')
            sys.exit(-1)
    
    f_temp = open( folder + '/temp.txt', mode="w", encoding="utf-8")
    f_humi = open( folder + '/humi.txt', mode="w", encoding="utf-8")
    f_pm25 = open( folder + '/pm25.txt', mode="w", encoding="utf-8")
    f_bat  = open( folder + '/battery.txt', mode="w", encoding="utf-8")
    f_vol  = open( folder + '/voltage.txt', mode="w", encoding="utf-8")
    f_current  = open( folder + '/current.txt', mode="w", encoding="utf-8")
    f_power  = open( folder + '/power.txt', mode="w", encoding="utf-8")

    pm2_5 = 0.0
    temp = 0.0
    humi = 0.0

    main_is_run = True
    timerun = TimeRun*60*60
    EndTime = int(time.time()) + timerun    
    state = {'dht': False,
            'pm25' : False}
    # loop
    try:
        # wait until next minute to start
        old_minute = int(getTime())
        if Debug: print('waiting until next minute to start')
        while int(getTime()) - old_minute < 1:
            time.sleep(1)
        print("-------------------- Bat dau thu nghiem trong {}s --------------------".format(str(timerun)))

        while main_is_run and (int(time.time()) < EndTime):
            # Start in new minute
            print('Start in new minute:' + getTime())
            start_peroid_time = int(round(time.time() * 1000))
            readSensor_minute = getTime()
            
            endTimeReadAllSensor = start_peroid_time + (ReadSensorInterval*60*1000/2)
            endTimeSendToServer  = start_peroid_time + (ReadSensorInterval*60*1000)
            
            # Read sensor in Interval/2
            data_report = {}
            data_report['Time'] = readSensor_minute
            
            # Read Battery:
            if UsePin:
                voltage = Battery.getBusVoltage_V()         # voltage on V- (load side)            
                current = Battery.getCurrent_mA()           # current in mA
                power = Battery.getPower_W()                # power in W
                percent = Battery.getPercent()    
                print('v={}V  i={}mA  p={}W  %={}%'.format(voltage,current,power,percent))        
                writeFile(f_vol, readSensor_minute, 'Voltage', voltage, 'V')
                writeFile(f_current, readSensor_minute, 'Current', current, 'mA')
                writeFile(f_power, readSensor_minute, 'Power', power, 'W')
                writeFile(f_bat, readSensor_minute, 'Battery', percent, '%')
                data_report['Battery(%)'] = percent

            state = {'dht': False,
                    'pm25' : False}
            next_reading = round(time.time()*1000)
            while (int(round(time.time() * 1000)) < endTimeReadAllSensor) and not checkReadAllSensorSuccess(state):
                if UsePM25 and state['pm25'] != True:
                    pm2_5, ok = PM2_5.getSensor()
                    if not ok:
                        print('Error read sensor: PM2.5')                
                    else:
                        if Debug: print('PM2.5:{} ug/m3'.format(pm2_5))
                        data_report['PM2.5(ug/m3)'] = pm2_5
                        writeFile(f_pm25, readSensor_minute, 'PM2.5', pm2_5, 'ug/m3')
                        state['pm25'] = True
                
                if UseDHT and state['dht'] != True:
                    temp, humi, ok = DHT.getSensor()
                    if not ok:
                        print('Error read sensor: DHT')                        
                    else:
                        if Debug: print('Temp:{} oC\nHumi:{} %'.format(temp, humi))
                        data_report['Temperature(oC)'] = temp
                        data_report['Humidity(%)'] = humi
                        writeFile(f_temp, readSensor_minute, 'Temperature', temp, 'oC')
                        writeFile(f_humi, readSensor_minute, 'Humidity', humi, '%')
                        state['dht'] = True
                
                # Sleep to read sensor
                # if SensorReadMode:
                next_reading += SENSOR_READ_INTERVAL + 50       # 50ms
                sleep_time = next_reading - round(time.time()*1000)
                if sleep_time > 0:
                    time.sleep(sleep_time/1000.0)                        
            
            # Get GPS
            if UseSim:
                gps, _ = sim.gps_get_data()
                data_report['GPS'] = gps

            # Send data to Server in Interval/2
            if UseWiFi or UseSim:
                # Encode the data of sensors to JSON format
                data_report_json = json.dumps(data_report)                     
                print('Send data to Server:' + URL)
                print(data_report_json)

                # Send data to Server in Interval/2
                while (int(round(time.time() * 1000)) + (HTTP_RESPONSE_TIMEOUT+ HTTP_CONNECT_TIMEOUT)*1000 < endTimeSendToServer):
                    ok = http_post(URL, ContentType, data_report_json, HTTP_CONNECT_TIMEOUT, HTTP_RESPONSE_TIMEOUT)
                    if not ok:
                        print('Error sending data to Server')
                    else:
                        print('Send to Server success')
                        break

            # wait until next ReadSensorInterval minute
            while int(getTime()) - int(readSensor_minute) < ReadSensorInterval:
                time.sleep(3)
        
    except KeyboardInterrupt:
        main_is_run = False

    # exit
    if UsePM25:
        PM2_5.closeSensor()
        del PM2_5
    if UseDHT:
        DHT.closeSensor()
        del DHT
    if UsePin:
        del Battery
    if UseSim:
        sim.gps_stop()
        sim.at_close()
        sim.power_down(POWER_KEY)
    sys.exit(0)
    