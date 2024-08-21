from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import time, csv, re
from datetime import datetime

class Mux:
    def __init__(self, uid, device, CR="\x0D"):
        self.uid = uid
        self.device = device
        self.CR = CR
        self.create_port()

    def create_port(self, ):
        self.ser = Serial(port=f"""/dev/{self.device}""",
                          baudrate=9600,
                          bytesize=EIGHTBITS,
                          parity=PARITY_NONE,
                          stopbits=STOPBITS_ONE,
                          timeout=0.2,
                          xonxoff=False,
                          rtscts=False,
                          dsrdtr=False)

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
        if not self.ser:
            self.create_port()
        if channel == "":
            data = f"""{pre}{len(self.uid)+5}{cmd}{self.uid}"""
        else:
            data = f"""{pre}{len(self.uid)+6}{cmd}{self.uid}{channel}"""
            print("....", data)
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
        return r.decode("utf-8").strip("\r")


    def get_all_weights(self):
        self.muxwrite(cmd="gl", pre="#")
        values = self.sanitize(mux_readout=self.muxread())
        return {f"{i:02}": values[i] for i in range(len(values))}





    def zero_scale(self, channel):
        self.muxwrite(pre="#", cmd="sz", channel=channel)
        if "OK" in self.muxread():
            print(f"""scale {channel} successfully calibrated""")
        else:
            print(f"""scale {channel} was not calibrated""")

    def zero_all_scales(self):
        for i in range(0, 8):
            self.zero_scale(channel=i)

    def create_csv(self, max_values=None):
        csv_file_name = f"""log_from_{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.csv"""
        with open(csv_file_name, mode="w", newline="") as csvfile:
            fieldnames = ["mux", "timestamp", "scale_00", "scale_01", "scale_02", "scale_03", "scale_04", "scale_05", "scale_06", "scale_07"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            counter = 0
            while True:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                w = self.get_all_weights()
                l = {"mux": self.uid, "timestamp": now, "scale_00": w["00"], "scale_01": w["01"], "scale_02": w["02"], "scale_03": w["03"], "scale_04": w["04"], "scale_05": w["05"], "scale_06": w["06"], "scale_07": w["07"]}
                writer.writerow(l)
                time.sleep(0.1)
                counter += 1

                if counter % 10 == 0:
                    print(f"""{counter}/{max_values} finished ...""")
                if counter == max_values and max_values != None:
                    print("we are done here")
                    return



con = Mux(device=f"ttyUSB0", uid="0120211005135155")
#con.zero_scale(3)
con.create_csv(max_values=20)
