from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import os, re, time
from datetime import datetime
from usbports import get_port
from environs import Env
 

class Mux:
    """
    output looks like this: [weights_1, weights_2, weights_3, weights_4, temp_1, temp_2, temp_3, temp_4]
    """
    def __init__(self, max_values=0, sleep_time=60):

        # Initialize the environment & read env file
        env = Env()
        env.read_env()

        # Initialize MUX
        self.UID = env("MUX")
        self.CR = "\x0D"
        self.create_port()
        self.COUNTER = 0
        self.MAX_VALUES = max_values
        self.SLEEP = sleep_time

    def create_port(self, ):
        port = get_port(devicetype="scale")
        self.ser = Serial(port=port, 
                          baudrate=9600, 
                          bytesize=EIGHTBITS, 
                          parity=PARITY_NONE, 
                          stopbits=STOPBITS_ONE, 
                          timeout=0.2, 
                          xonxoff=False, 
                          rtscts=False, 
                          dsrdtr=False)
        print("scales port was initiated ...")

    @staticmethod
    def calculate_crc(data):
        crc = 0
        for byte in data:
            crc ^= ord(byte)
        crc_hex = format(crc, "02x").upper()
        return crc_hex

    def sanitize(self, mux_readout):
        # Regular expression to match the required pattern
        pattern = r"([-]?\d{5})\.(\d{3})"
        # Find all matches in the serial output
        matches = re.findall(pattern, mux_readout)

        ## sometimes more scales are returned than physically exist
        # matches = matches[]
        results = []
        # Process each match
        for match in matches:
            # Combine the parts into a single string
            result = f"{match[0]}.{match[1]}"
            results.append(result)
        return results

    def muxwrite(self, pre, cmd, channel=""):
        if channel == "":
            data = f"""{pre}{len(self.UID)+5}{cmd}{self.UID}"""
        else:
            data = f"""{pre}{len(self.UID)+6}{cmd}{self.UID}{channel}"""
        CC = self.calculate_crc(data)
        cmd = f"""{data}{CC}{self.CR}"""
        # print("mux write:", cmd.encode("utf-8"))
        return self.ser.write(cmd.encode("utf-8"))

    def muxread(self):
        """
        a little sleeping time is added, so the next cmd cannot be issued before read is finished
        duration = transmitted bytes x bits per byte / baudrate
        for longest possible message (105 chars):
        105 x 10 / 9600 = 0.109 [s]
        """
        r = self.ser.read_until(self.CR)
        return r.decode("utf-8").strip("\r") 

    def get_all_weights(self):
        if self.COUNTER != 0:
            time.sleep(self.SLEEP)
        
        if self.MAX_VALUES != 0: ## if it is 0 continuos polling
            self.COUNTER += 1
            if self.COUNTER == self.MAX_VALUES:
                print("counter ran out ...")
                exit()
        self.muxwrite(cmd="gl", pre="#")
        r = self.muxread()
        values = self.sanitize(mux_readout=r)
        return {f"{i:02}": values[i] for i in range(len(values))}

    def zero_scale(self, channel):
        w = self.muxwrite(pre="#", cmd="sz", channel=channel)
        r = self.muxread()
        time.sleep(2)
        if "OK" in r:
            print(f"""scale {channel} successfully calibrated""")
        else:
            print(f"""scale {channel} was not calibrated""")

    def zero_all_scales(self):
        for i in [0, 1]:
            self.zero_scale(channel=i)
        
    def get_revision(self):
        self.muxwrite(cmd="gr", pre="#")
        values = self.muxread()
        print("---- values ---->", values)
        return values.replace("#06", "")


if __name__ == "__main__":
    mux = Mux()
    r = mux.get_revision()
    print("test successful, revision of the mux:", r)
    s = mux.get_all_weights()
    print("tested for weights:", s)