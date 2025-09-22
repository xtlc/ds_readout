from pathlib import Path
import time

class PT100:
    def __init__(self):
        from environs import Env
        env = Env()
        env.read_env()
        BASEDIR = Path("/sys/bus/w1/devices/")
        self.sensors = {}
        self.sensors["in_ri"] =  BASEDIR.joinpath(f"""28-{env("DS18B20_IN_RIGHT")}""", "w1_slave")
        self.sensors["out_ri"] = BASEDIR.joinpath(f"""28-{env("DS18B20_OUT_RIGHT")}""", "w1_slave")
        self.sensors["in_le"] =  BASEDIR.joinpath(f"""28-{env("DS18B20_IN_LEFT")}""", "w1_slave")
        self.sensors["out_le"] = BASEDIR.joinpath(f"""28-{env("DS18B20_OUT_LEFT")}""", "w1_slave")

    def get_temps(self, testing=False):
        values = {}
        for name, address in self.sensors.items():
            try:
                with open(address, "r") as w1s:
                    data = w1s.read()
                    values[name] =  float(data.split("t=")[1])/1000
            except Exception as E:
                if testing:
                    print("not working because of", E)
                values[name] = float("nan")
        return values
                

if __name__ == "__main__":

    print("------------------------------ T E S T I N G ----------------------------------------------")
    pt100s = PT100()

    while True:
        t = pt100s.get_temps(testing=True)
        print(t)
        time.sleep(1)
