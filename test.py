import serial
import time
from scales import Mux
from ens210 import Temp
from pt100 import PT100

pt = PT100(PT100_WATER_IN_RIGHT="0000006a2c70", PT100_WATER_OUT_RIGHT="0000006ada1a", PT100_WATER_IN_LEFT="d5d3f91d64ff", PT100_WATER_OUT_LEFT="a7d0f91d64ff")
while True:
     print(pt.get_temps())
     time.sleep(2)

## to test the ens210
#t = Temp(device="ttyUSB1")
#while True:
#     print(t.get_all_temps())
#     time.sleep(2)
#exit()


## to test the scales
#s = Mux(device="ttyUSB0", uid="0020240425142741", number_of_scales=2, max_values=0, sleep_time=0)
#while True:
#     print(s.get_revision())
#     time.sleep(2)
#exit()


device_0 = f"ttyUSB0"
device_1 = f"ttyUSB1"

se0 = serial.Serial(port=f"""/dev/{device_0}""",
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=2,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False)


se1 = serial.Serial(port=f"""/dev/{device_1}""",
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=2,
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False)


msg = "HELLO RApha"

m =se0.write(msg.encode("utf-8"))
print("number of bytes written:", m)

r = se1.read(12)
print("->", r.decode('utf-8').strip('\r'))
