import os
import sys
import time
import json
import requests
import argparse
import board
from datetime import datetime

from sensor import ze12
from sensor import ze15
from sensor import ze25
from sensor import zh03b
from sensor import wv20
from sensor import dht

startTime = datetime.now().strftime("%Y%m%d%H%M")

parser = argparse.ArgumentParser()
parser.add_argument('-all',     help='Use all sensor and http', action='store_true')
parser.add_argument('-dht',     help='Use DHT.      Jump Vcc-P-Gnd:1-12-9', action='store_true')
parser.add_argument('-pm25',    help='Use PM2.5.    Jump V-Tx-Rx-G:2-8-10-14', action='store_true')
parser.add_argument('-so2',     help='Use SO2.      Jump V-Tx-Rx-G:2-27-28-25', action='store_true')
parser.add_argument('-co2',     help='Use CO2.      Jump V-Tx-Rx-G:17-7-29-30', action='store_true')
parser.add_argument('-co',      help='Use CO.       Jump V-Tx-Rx-G:2-24-21-20', action='store_true')
parser.add_argument('-o3',      help='Use O3.       Jump V-Tx-Rx-G:2-32-33-34', action='store_true')
parser.add_argument('-http',    help='Enable post data to Server via HTTP', action='store_true')
parser.add_argument('-d', '--debug', help='enable/disable Debug', action='store_true')
parser.add_argument('-t', '--time', help='measuring time (h)' , type=int, default=1)
parser.add_argument('-i', '--interval', help='measuring interval time (min)' , type=int, default=1)

option = parser.parse_args()

UseAll = option.all
UseHTTP = option.http or UseAll
UseDHT = option.dht or UseAll
UseCO2 = option.co2 or UseAll
UseSO2 = option.so2 or UseAll
UseCO = option.co or UseAll
UseO3 = option.o3 or UseAll
UsePM25 = option.pm25 or UseAll
SensorReadMode = 1
Debug = option.debug
TimeRun = option.time
ReadSensorInterval = option.interval

folder = startTime + '_' + str(TimeRun) + 'h'
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

# Config Sensors
CO2 = wv20.sensor()
SO2 = ze12.sensor()
CO = ze15.sensor()
O3 = ze25.sensor()
PM2_5 = zh03b.sensor()
DHT = dht.sensor()

DHT_PIN = board.D18
PORT_PM2_5 = '/dev/ttyAMA0'
PORT_SO2 = '/dev/ttyAMA1'
PORT_CO2 = '/dev/ttyAMA2'
PORT_CO = '/dev/ttyAMA3'
PORT_O3 = '/dev/ttyAMA4'

SENSOR_READ_INTERVAL = 0 #ms
if UseCO and CO.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = CO.ACTIVE_UPLOAD_INTERVAL
if UseCO2 and CO2.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = CO2.ACTIVE_UPLOAD_INTERVAL
if UseSO2 and SO2.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = SO2.ACTIVE_UPLOAD_INTERVAL
if UseO3 and O3.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = O3.ACTIVE_UPLOAD_INTERVAL
if UsePM25 and PM2_5.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = PM2_5.ACTIVE_UPLOAD_INTERVAL
if UseDHT and DHT.ACTIVE_UPLOAD_INTERVAL > SENSOR_READ_INTERVAL:
    SENSOR_READ_INTERVAL = DHT.ACTIVE_UPLOAD_INTERVAL

# Global variables
DEVICE_ID = 'Station1'
data_report = {
    'ID': DEVICE_ID,
    'GPS': '',
    'Time': '',
    'Temperature(oC)': 0.0,
    'Humidity(%)': 0.0,    
    'PM2.5(ug/m3)': 0.0,
    'SO2(ug/m3)': 0.0,
    'CO(ug/m3)': 0.0,
    'O3(ug/m3)': 0.0,
    'CO2(ug/m3)': 0.0
}
data_report_json = ''

False_SensorReadState = {
    'dht' : False,    
    'pm25' : False,
    'so2' : False,
    'co2' : False,
    'co' : False,
    'o3' : False
}

def setReadAllSensorFalse(state):
    state['dht'] = False
    state['pm25'] = False
    state['so2'] = False
    state['co2'] = False
    state['co'] = False
    state['o3'] = False

def checkReadAllSensorSuccess(state):
    if UseDHT:
        if state['dht'] != True:
            return False
    if UsePM25:
        if state['pm25'] != True:
            return False
    if UseSO2:
        if state['so2'] != True:
            return False
    if UseCO2:
        if state['co2'] != True:
            return False
    if UseCO:
        if state['co'] != True:
            return False
    if UseO3:
        if state['o3'] != True:
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
    if not wifi_http_post(url, contentType, json_data, connTimeout, recvTimeout):
        if Debug: print('WiFi: Send data to Server error.')
        # if not sim.http_post(url, contentType, json_data, connTimeout, recvTimeout):
        #     if Debug: print('Error: Send via Sim error.')
        return False
    return True

# ----------------- write file funcs ------------------------
# 
def writeFile(file, timeMinute, name, value, unit, status, station):
    file.write('{},{},{},{},{},{}\n'.format(timeMinute, name, value, unit, status, station))

def getTime():
    return datetime.now().strftime("%Y%m%d%H%M")

# ----------------- Main ------------------------
# 
if __name__ == "__main__":
    if UseSO2:
        ok = SO2.initSensor(PORT_SO2, SensorReadMode)
        if not ok:
            print('init SO2 error')
            sys.exit(-1)
    if UseCO:
        ok = CO.initSensor(PORT_CO, SensorReadMode)
        if not ok:
            print('init CO error')
            sys.exit(-1)
    if UseO3:
        ok = O3.initSensor(PORT_O3, SensorReadMode)
        if not ok:
            print('init O3 error')
            sys.exit(-1)
    if UsePM25:
        ok = PM2_5.initSensor(PORT_PM2_5, SensorReadMode)
        if not ok:
            print('init PM2.5 error')
            sys.exit(-1)
    if UseCO2:
        ok = CO2.initSensor(PORT_CO2, SensorReadMode)
        if not ok:
            print('init CO2 error')
            sys.exit(-1)
    if UseDHT:
        ok = DHT.initSensor(DHT_PIN)
        if not ok:
            print('init DHT error')
            sys.exit(-1)
    
    f_temp = open( folder + '/temp.txt', mode="w", encoding="utf-8")
    f_humi = open( folder + '/humi.txt', mode="w", encoding="utf-8")
    f_pm25 = open( folder + '/pm25.txt', mode="w", encoding="utf-8")
    f_so2 = open( folder + '/so2.txt', mode="w", encoding="utf-8")
    f_co2 = open( folder + '/co2.txt', mode="w", encoding="utf-8")
    f_co = open( folder + '/co.txt', mode="w", encoding="utf-8")
    f_o3 = open( folder + '/o3.txt', mode="w", encoding="utf-8")

    so2 = 0.0
    co2 = 0.0
    co = 0.0
    o3 = 0.0
    pm2_5 = 0.0
    temp = 0.0
    humi = 0.0

    main_is_run = True
    timerun = TimeRun*60*60
    EndTime = int(time.time()) + timerun    
    state = False_SensorReadState
    # loop
    try:
        # wait uintil next minute to start
        old_minute = int(getTime())
        while int(getTime()) - old_minute < 1:
            time.sleep(1)
        print("-------------------- Bat dau thu nghiem trong {}s --------------------".format(str(timerun)))

        while main_is_run and (int(time.time()) < EndTime):
            # Start in new minute
            print('Start in new minute:' + getTime())
            start_peroid_time = int(round(time.time() * 1000))
            readSensor_minute = getTime()
            data_report['Time'] = readSensor_minute

            # Read sensor in Interval/2
            endTimeReadAllSensor = start_peroid_time + (ReadSensorInterval*60*1000/2)                     
            setReadAllSensorFalse(state)            
            next_reading = round(time.time()*1000)
            while (int(round(time.time() * 1000)) < endTimeReadAllSensor) and not checkReadAllSensorSuccess(state):
                if UseSO2 and state['so2'] == False:
                    so2, ok = SO2.getSensor()
                    if not ok:
                        if Debug: print('Error read sensor: SO2')
                        continue                
                    else:
                        if Debug: print('SO2:{} ug/m3'.format(so2))
                        data_report['SO2(ug/m3)'] = so2
                        writeFile(f_so2, readSensor_minute, 'SO2', so2, 'ug/m3', 'Good', DEVICE_ID)
                        state['so2'] = True
                
                if UseCO2 and state['co2'] == False:
                    co2, ok = CO2.getSensor()
                    if not ok:
                        if Debug: print('Error read sensor: CO2')
                        continue                 
                    else:
                        if Debug: print('CO2:{} ug/m3'.format(co2))
                        data_report['CO2(ug/m3)'] = co2
                        writeFile(f_co2, readSensor_minute, 'CO2', co2, 'ug/m3', 'Good', DEVICE_ID)
                        state['co2'] = True

                if UseCO and state['co'] == False:
                    co, ok = CO.getSensor()
                    if not ok:
                        if Debug: print('Error read sensor: CO')
                        continue              
                    else:
                        if Debug: print('CO:{} ug/m3'.format(co))
                        data_report['CO(ug/m3)'] = co
                        writeFile(f_co, readSensor_minute, 'CO', co, 'ug/m3', 'Good', DEVICE_ID)
                        state['co'] = True

                if UseO3 and state['o3'] == False:
                    o3, ok = O3.getSensor()
                    if not ok:
                        if Debug: print('Error read sensor: O3')
                        continue           
                    else:
                        if Debug: print('O3:{} ug/m3'.format(o3))
                        data_report['O3(ug/m3)'] = o3
                        writeFile(f_o3, readSensor_minute, 'O3', o3, 'ug/m3', 'Good', DEVICE_ID)
                        state['o3'] = True
                
                if UsePM25 and state['pm25'] == False:
                    pm2_5, ok = PM2_5.getSensor()
                    if not ok:
                        if Debug: print('Error read sensor: PM2.5')
                        continue     
                    else:
                        if Debug: print('PM2.5:{} ug/m3'.format(pm2_5))
                        data_report['PM2.5(ug/m3)'] = pm2_5
                        writeFile(f_pm25, readSensor_minute, 'PM2.5', pm2_5, 'ug/m3', 'Good', DEVICE_ID)
                        state['pm25'] = True
                
                if UseDHT and state['dht'] == False:
                    temp, humi, ok = DHT.getSensor()
                    if not ok:
                        if Debug: print('Error read sensor: DHT')
                        continue
                    else:
                        if Debug: print('Temp:{} *C     Humi:{} %'.format(temp, humi))
                        data_report['Temperature(oC)'] = temp
                        data_report['Humidity(%)'] = humi
                        writeFile(f_temp, readSensor_minute, 'Temperature', temp, 'oC', '', DEVICE_ID)
                        writeFile(f_humi, readSensor_minute, 'Humidity', humi, '%', '', DEVICE_ID)
                        state['dht'] = True
                
                # Sleep to read sensor
                # if SensorReadMode:
                next_reading += SENSOR_READ_INTERVAL + 50       # 50ms
                sleep_time = next_reading - round(time.time()*1000)
                if sleep_time > 0:
                    time.sleep(sleep_time/1000.0)
            
            # Encode the data of sensors to JSON format
            data_report_json = json.dumps(data_report)
            # Sending data to Server
            # if Debug:
            print('Send data to Server:' + URL)
            print(data_report_json)
            
            if UseHTTP:
                ok = http_post(URL, ContentType, data_report_json, HTTP_CONNECT_TIMEOUT, HTTP_RESPONSE_TIMEOUT)
                if not ok:
                    print('Error sending data to Server')
                else:
                    print('Send to Server success')

            # wait uintil next ReadSensorInterval minute
            while int(getTime()) - int(readSensor_minute) < ReadSensorInterval:
                time.sleep(3)
        
    except KeyboardInterrupt:
        main_is_run = False

    # exit
    if UseSO2:
        SO2.closeSensor()
        del SO2
    if UseCO:
        CO.closeSensor()
        del CO
    if UseO3:
        O3.closeSensor()
        del O3
    if UsePM25:
        PM2_5.closeSensor()
        del PM2_5
    if UseCO2:
        CO2.closeSensor()
        del CO2
    if UseDHT:
        DHT.closeSensor()
        del DHT
    sys.exit(0)
    