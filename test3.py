import datetime

D = str(datetime.datetime.now())
D = D.split(' ')[0]
Y,M,D = D.split('-')
ID = 'PF' + Y[2:] + M + D+'-'

print(ID)