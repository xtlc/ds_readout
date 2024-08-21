import serial

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
