from pathlib import Path

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
    for item in BASEDIR.iterdir():
        if item.is_dir():
            print(f"""found sensor: {item.name}""")
    print("----------------------------------------------------------------------------")
    f = PT100(PT100_WATER_IN_RIGHT="0000006a2c70", PT100_WATER_OUT_RIGHT="0000006ada1a", PT100_WATER_IN_LEFT="d5d3f91d64ff", PT100_WATER_OUT_LEFT="a7d0f91d64ff") ## for
    while True:
        t = f.get_temps()
        print(t)