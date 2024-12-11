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
            # print("working on address", address)
            with open(address, "r") as w1s:
                data = w1s.read()
                try:
                    values[name] =  float(data.split("t=")[1])/1000
                except Exception as E:
                    print("could not read pt100 values for", name, "because of:", E)
                    return None
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

## sensor 1
## 
## /sys/devices/w1_bus_master1/28-0000006a2c70 $ cat w1_slave 
## 4c 01 7f 80 7f ff 04 10 7a : crc=7a YES
## 4c 01 7f 80 7f ff 04 10 7a t=20750
## 
## 
## sensor 2
## 
## rabaton@raspberrypi:/sys/bus/w1/devices $ ls -la
## insgesamt 0
## drwxr-xr-x 2 root root 0  4. Dez 12:06 .
## drwxr-xr-x 4 root root 0  4. Dez 12:03 ..
## lrwxrwxrwx 1 root root 0  4. Dez 12:46 28-0000006a2c70 -> ../../../devices/w1_bus_master1/28-0000006a2c70
## lrwxrwxrwx 1 root root 0  4. Dez 12:46 28-0000006ada1a -> ../../../devices/w1_bus_master1/28-0000006ada1a
## lrwxrwxrwx 1 root root 0  4. Dez 12:06 w1_bus_master1 -> ../../../devices/w1_bus_master1
## rabaton@raspberrypi:/sys/bus/w1/devices $ cd 28-0000006ada1a/
## rabaton@raspberrypi:/sys/bus/w1/devices/28-0000006ada1a $ cat w1_slave 
## 51 01 7f 80 7f ff 0f 10 71 : crc=71 YES
## 51 01 7f 80 7f ff 0f 10 71 t=21062
