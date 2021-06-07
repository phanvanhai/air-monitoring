import numpy as np
import matplotlib.pyplot as plt
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

minimum = np.min([minimum1, minimum2])
maximum = np.max([maximum1, maximum2])

result = scipy.stats.linregress(value1, value2)
a = round(result.slope, 2)
b = round(result.intercept,2)
r = round(result.rvalue,2)
liner = 'Slope:{}    Intercept:{}    Relationship:{}\n Calibration equaltion: y = {}*x + {}'.format(a,b,r,a,b)

plt.ylabel(unitSensor1)
plt.xlabel(unitSensor1)
plt.title(nameSensor1 + '\n' + liner)
plt.grid(color="grey", linewidth=1, axis="both", alpha=0.1)

# plot point
plt.scatter(value1, value2, 10, 'r')

x = np.linspace(minimum - 3,maximum + 3,2)
y = a*x+b
plt.plot(x, y, '-g', label='y={}x+{}'.format(a,b))

plt.show()

