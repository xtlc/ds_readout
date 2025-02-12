from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import os, time 

class Temp:
    def __init__(self, device, sensors):
        self.dev = f"""/dev/{device}""" ##f os.name == "nt": dev = f"""{self.DEVICE}"""
        self.create_port()
        self.CR = "\x0D"
        self.sensors = sensors
        # sensors = {"top_left": "g", "bot_left": "d", "top_mid": "j", "bot_mid": "i", "top_right": "m", "bot_right": "k"}

    def create_port(self, ):
        self.ser = Serial(port=self.dev, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=.2, xonxoff=False, rtscts=False, dsrdtr=False)

    def get_all_temps(self):
        values = {"temp_top_right": None, "temp_bot_right": None, "temp_top_mid": None, "temp_bot_mid": None, "temp_top_left": None, "temp_bot_left": None, 
                  "humid_top_right": None, "humid_bot_right": None, "humid_top_mid": None, "humid_bot_mid": None, "humid_top_left": None, "humid_bot_left": None}

        for position, sensor in self.sensors.items():
            self.serwrite(cmd=sensor)
            time.sleep(.1)
            _, values[f"temp_{position}"], values[f"humid_{position}"] = self.sanitize(self.serread())
        return values

    def serwrite(self, cmd):
        return self.ser.write(cmd.encode("utf-8"))

    def serread(self):
        r = self.ser.read_until(self.CR)
        return r.decode("utf-8").strip("\r\n") 
    
    def sanitize(self, readout):
        """
        returns: sensor, temp, humid
        """
        try:
            s, t, h = readout.split(" ")
            return s, float(t), float(h)
        except:
            return None, float("nan"), float("nan")


if __name__ == "__main__":
    ENS210s = {"top_left": "g", "bot_left": "d", "top_mid": "j", "bot_mid": "i", "top_right": "m", "bot_right": "k"}
    t = Temp(device="ttyUSB1", sensors=ENS210s)
    while True:
        print(t.get_all_temps())
        time.sleep(1)
