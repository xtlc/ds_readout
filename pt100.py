from pathlib import Path
import time

BASEDIR = Path("/sys/bus/w1/devices/")

class PT100:
    def __init__(self, PT100_WATER_IN_RIGHT=None, PT100_WATER_OUT_RIGHT=None, PT100_WATER_IN_LEFT=None, PT100_WATER_OUT_LEFT=None):
        self.sensors = {}
        if PT100_WATER_IN_RIGHT:
            self.sensors["in_ri"] =  BASEDIR.joinpath(f"""28-{PT100_WATER_IN_RIGHT}""", "w1_slave")
        if PT100_WATER_OUT_RIGHT:
            self.sensors["out_ri"] = BASEDIR.joinpath(f"""28-{PT100_WATER_OUT_RIGHT}""", "w1_slave")
        if PT100_WATER_IN_LEFT:
            self.sensors["in_le"] =  BASEDIR.joinpath(f"""28-{PT100_WATER_IN_LEFT}""", "w1_slave")
        if PT100_WATER_OUT_LEFT:
            self.sensors["out_le"] = BASEDIR.joinpath(f"""28-{PT100_WATER_OUT_LEFT}""", "w1_slave")

    def get_temps(self):
        values = {}
        for name, address in self.sensors.items():
            try:
                with open(address, "r") as w1s:
                    data = w1s.read()
                    values[name] =  float(data.split("t=")[1])/1000
            except Exception as E:
                values[name] = float("nan")
        return values
                
                


if __name__ == "__main__":
    print("Test mode running ...")    # You can call your function here if needed
    sensors = []
    for item in BASEDIR.iterdir():
        if item.is_dir() and item.name.startswith("28-"):
            sensors.append(item.name[3:])
            print(f"""found sensor: {item.name}""")
    print("------------------------------ T E S T I N G ----------------------------------------------")
    print("using", sensors)
    # f = PT100(PT100_WATER_IN_RIGHT="0000006a2c70", PT100_WATER_OUT_RIGHT="0000006ada1a", PT100_WATER_IN_LEFT="d5d3f91d64ff", PT100_WATER_OUT_LEFT="a7d0f91d64ff") ## for
    # DS18B20s = {"in_ri": , "out_ri": env("DS18B20_OUT_RIGHT"), "in_le":env("DS18B20_IN_LEFT"), "out_le": env("DS18B20_OUT_LEFT")}
    pt100s = PT100(PT100_WATER_IN_LEFT=env("DS18B20_IN_LEFT"), PT100_WATER_OUT_LEFT=env("DS18B20_OUT_LEFT"),
                   PT100_WATER_IN_RIGHT=env("DS18B20_IN_RIGHT"), PT100_WATER_OUT_RIGHT=env("DS18B20_OUT_RIGHT"))


    while True:
        t = pt100s.get_temps()
        print(t)
        time.sleep(1)