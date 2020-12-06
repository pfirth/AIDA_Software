import numpy as np
for i in range(21,30,1):
    print(str(i)+'.0')

for i in np.arange(21.0, 23.0, 0.1):
    command = 'P' + "{:.1f}".format(i) + '\r'
    command = str.encode(command)

    print(command)