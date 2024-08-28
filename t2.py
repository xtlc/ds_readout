from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import time, csv, re
from datetime import datetime, timezone


class Mux:
    def __init__(self, uid, device, number_of_scales):
        self.uid = uid
        self.device = device
        self.CR = "\x0D"
        self.create_port()
        self.SCALES = number_of_scales

    def create_port(self, ):
        self.ser = Serial(port=f"""/dev/{self.device}""", baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=0.2, xonxoff=False, rtscts=False, dsrdtr=False)

    @staticmethod
    def calculate_crc(data):
        crc = 0
        for byte in data:
            crc ^= ord(byte)
        crc_hex = format(crc, "02x")
        return crc_hex

    @staticmethod
    def sanitize(mux_readout):
        # Regular expression to match the required pattern
        pattern = r"([-]?\d{5})\.(\d{3})"
        # Find all matches in the serial output
        matches = re.findall(pattern, mux_readout)
        results = []
        # Process each match
        for match in matches:
            # Combine the parts into a single string
            result = f"{match[0]}.{match[1]}"
            results.append(result)
        return results

    def muxwrite(self, pre, cmd, channel=""):
        if channel == "":
            data = f"""{pre}{len(self.uid)+5}{cmd}{self.uid}"""
        else:
            data = f"""{pre}{len(self.uid)+6}{cmd}{self.uid}{channel}"""
        CC = self.calculate_crc(data)
        cmd = f"""{data}{CC}{self.CR}"""
        return self.ser.write(cmd.encode("utf-8"))

    def muxread(self):
        """
        a little sleeping time is added, so the next cmd cannot be issued before read is finished
        duration = transmitted bytes x bits per byte / baudrate
        for longest possible message (105 chars):
        105 x 10 / 9600 = 0.109 [s]
        """
        r = self.ser.read_until(self.CR)
        time.sleep(0.2)
        print(r.decode("utf-8").strip("\r"))
        return r.decode("utf-8").strip("\r")
        

    def get_revision(self):
        self.muxwrite(cmd="gr", pre="#")
        values = self.sanitize(mux_readout=self.muxread())
        return values.replace("#06", "")


    def get_all_weights(self):
        self.muxwrite(cmd="gl", pre="#")
        values = self.sanitize(mux_readout=self.muxread())
        return {f"{i:02}": values[i] for i in range(len(values))}

mux_4kg_1 = "0120211005135902"
mux_8kg_1 = "0020240425142741"

m = Mux(uid=mux_8kg_1, device=f"ttyUSB0", number_of_scales=4)
m.get_revision()

