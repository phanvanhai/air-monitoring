import numpy as np
import matplotlib.pyplot as plt
from numpy.lib.function_base import average
import argparse
import scipy.stats

parser = argparse.ArgumentParser()
parser.add_argument('-f1', '--file1', help='input file name' ,default='sensor.txt')
parser.add_argument('-f2', '--file2', help='input file name' ,default='sensor.txt')
args = parser.parse_args()
fileName1 = args.file1
fileName2 = args.file2

start_time1 = []
nameSensor1 = ''
value1 = []
unitSensor1 = ''

start_time2 = []
nameSensor2 = ''
value2 = []
unitSensor2 = ''

with open(fileName1, mode="r", encoding="utf-8") as f:
    data = f.readlines()    
    for d in data:
        d = d.split(",")
        if len(d) >= 4:
            start_time1.append(int(d[0]))
            nameSensor1 = d[1]
            value1.append(float(d[2]))    
            unitSensor1 = d[3]

start_time1 = np.array(start_time1)
value1 = np.array(value1)

maximum1 = np.max(value1)
minimum1 = np.min(value1)
min_max_info1 = 'sum={} min={} max={} avr={}'.format(len(value1), minimum1, maximum1, round(average(value1), 1))

with open(fileName2, mode="r", encoding="utf-8") as f:
    data = f.readlines()    
    for d in data:
        d = d.split(",")
        if len(d) >= 4:
            start_time2.append(int(d[0]))
            nameSensor2 = d[1]
            value2.append(float(d[2]))    
            unitSensor2 = d[3]

start_time2 = np.array(start_time2)
value2 = np.array(value2)

maximum2 = np.max(value2)
minimum2 = np.min(value2)
min_max_info2 = 'sum={} min={} max={} avr={}'.format(len(value2), minimum2, maximum2, round(average(value2), 1))


result = scipy.stats.linregress(value1, value2)
liner = 'y = {}.x + {}   ~ r = {}'.format(round(result.slope, 2), round(result.intercept,2), round(result.rvalue,2))

plt.ylabel(unitSensor1)
plt.xlabel("YY-mm-DD-HH-MM")
plt.title(nameSensor1 + '\n' + liner)
plt.grid(color="grey", linewidth=1, axis="both", alpha=0.1)

# plot line
plt.plot(value1, color="orange")
plt.plot(value2, color="green")
plt.legend(['sensor can calib:' + min_max_info1, 'sensor cua tram:' + min_max_info2])
# plot point
# plt.scatter(start_time1, value1, 3, 'r')
# plt.scatter(start_time2, value2, 3, 'g')


plt.show()

