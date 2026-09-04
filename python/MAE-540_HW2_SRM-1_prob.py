import matplotlib.pyplot as plt
import numpy as np

fname = 'C:/Anaconda3/My_Scripts/SRM-1.csv'
data = np.genfromtxt(fname, delimiter=',', names=True)
Time = data['Time']
Time = Time[:265]
Pressure = data['Pressure']
Thrust = data['Thrust']
avg_Thrust = 0
for T in Thrust:
    avg_Thrust += T
avg_Thrust = avg_Thrust/len(Thrust)

Thrust = Thrust[:265]
MF = data['MassFlowrate']
mp = 1106594  # lbm
g0 = 32.2  # ft/s


def Traprule(X, Y):
    areasum = 0
    for k in range(1, len(X)):
        dx = X[k] - X[k-1]
        dy = Y[k-1] + Y[k]
        arean = (dy/2)*dx
        areasum += arean
    return areasum


It = Traprule(Time, Thrust)
Isp = It/(mp*g0)
print('It = ', It, ' lbf-sec')
print('Is = ', Isp, ' sec')
print('Average Thrust = ', avg_Thrust, ' lbf')
plt.figure()
plt.title('Time vs. Thrust')
plt.plot(Time, Thrust)
plt.xlabel('Time (sec)')
plt.ylabel('Thrust (lbf)')
plt.grid()
plt.savefig('MAE-540_HW2_SRM-1_prob_fig.png')
