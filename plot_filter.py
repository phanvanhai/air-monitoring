import numpy as np
import matplotlib.pyplot as plt
from numpy.lib.function_base import average
import argparse

from scipy.signal import savgol_filter

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', help='input file name' ,default='sensor.txt')
args = parser.parse_args()
fileName = args.file

start_time = []
nameSensor = ''
value = []
unitSensor = ''

v_filter = 0.0
with open(fileName, mode="r", encoding="utf-8") as f:
    data = f.readlines()    
    for d in data:
        d = d.split(",")
        if len(d) >= 4:
            v = float(d[2])
            if v_filter == 0:
                v_filter = v
            else:
                if 1.0*v/v_filter >= 0.7 and 1.0*v/v_filter <= 1.3:                    
                    start_time.append(int(d[0]))
                    nameSensor = d[1]
                    value.append(float(d[2]))    
                    unitSensor = d[3]

start_time = np.array(start_time)
value = np.array(value)

maximum1 = np.max(value)
minimum1 = np.min(value)
min_max_info = 'sum={} min={} max={} avr={}'.format(len(value), minimum1, maximum1, round(average(value), 1))
# plt.legend([legend1])

plt.ylabel(unitSensor)
plt.xlabel("YY-mm-DD-HH-MM")
plt.title(nameSensor + ':' + min_max_info)
plt.grid(color="grey", linewidth=1, axis="both", alpha=0.1)

# plot line
plt.plot(value, color="orange")

yhat = savgol_filter(value, 51, 3) # window size 51, polynomial order 3
plt.plot(yhat, color="red")
# plot point
# plt.scatter(start_time, value, 3, 'g')

plt.show()

