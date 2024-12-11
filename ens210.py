from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import os, time 

class Temp:
    def __init__(self, device, ):
        self.DEVICE = device
        self.create_port()
        self.CR = "\x0D"
        self.sensors = self.get_all_temps()
        # print("available temp sensors:", self.sensors)
    
    def create_port(self, ):
        if os.name == "nt":
            dev = f"""{self.DEVICE}"""
        else:
            dev = f"""/dev/{self.DEVICE}"""
        self.ser = Serial(port=dev, 
                          baudrate=9600, 
                          bytesize=EIGHTBITS, 
                          parity=PARITY_NONE, 
                          stopbits=STOPBITS_ONE, 
                          timeout=0.2, 
                          xonxoff=False, 
                          rtscts=False, 
                          dsrdtr=False)

    def get_all_temps(self):
        sensors = []
        for i in ["d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",]:
            self.serwrite(cmd=i)
            time.sleep(0.1)
            try:
                values = self.sanitize(self.serread())
                sensors.append({"sensor": values["sensor"], "temperature": values["temp"], "humidity": values["humid"]})
            except (IndexError, ValueError):
                pass
        return sensors
    
    def serwrite(self, cmd):
        return self.ser.write(cmd.encode("utf-8"))

    def serread(self):
        r = self.ser.read_until(self.CR)
        return r.decode("utf-8").strip("\r\n") 
    
    def sanitize(self, readout):
        print(readout)
        tmp = readout.split(" ")
        return {"sensor": int(tmp[0]), "temp": float(tmp[1]), "humid": float(tmp[2])}


if __name__ == "__main__":
    t = Temp(device="ttyUSB0")
    while True:
        print(t.get_all_temps())
        time.sleep(1)
