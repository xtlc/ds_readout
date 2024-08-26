from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import time, csv, re
from environs import Env
from influxdb_client_3 import InfluxDBClient3, Point
from datetime import datetime, timezone


# Initialize the environment
env = Env()

# Read the .env file
env.read_env()

# InfluxDB parameters
token = env("INFLUX_TOKEN")
org = "abaton_influx"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
bucket = env("BUCKET")

client = InfluxDBClient3(host=host, database=bucket, token=token, org=org)





class Mux:
    def __init__(self, uid, device):
        self.uid = uid
        self.device = device
        self.CR = "\x0D"
        self.create_port()

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

    def to_influx(self, client):
        counter = 0
        while True:
            print(f"\r{counter} measurement ongoing ...", end="")
            for scale, weight in self.get_all_weights().items():
                p = Point("digisense_test_1").field(f"scale_{scale}", float(weight)*1000).time(datetime.utcnow())
                client.write(record=p)
            time.sleep(60)

       

    def create_csv(self, max_values=None):
        csv_file_name = f"""log_from_{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.csv"""
        BOLD = "\033[1m"
        RED = "\033[31m"
        RESET = "\033[0m"
        print(f"""csv file {csv_file_name} is being written ...\n""")
        with open(csv_file_name, mode="w", newline="") as csvfile:
            fieldnames = ["mux", "timestamp", *[f"scale_{i:02}" for i in range(8)]]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            counter = 0
            while True:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                w = self.get_all_weights()
                datarow = {"mux": self.uid, "timestamp": now,  **{f"scale_{i:02}": w[f"{i:02}"] for i in range(8)}}
                writer.writerow(datarow)
                time.sleep(0.1)
                counter += 1
                scale_string = "  |  ".join([f"""{BOLD}{RED}{key}:{RESET} {datarow[key]}kg""" for key in datarow.keys() if key not in ["mux", "timestamp"]])
                m = f"""0{len(str(max_values))}"""
                if max_values != None:
                    print(f"""\r{counter:{m}} / {max_values:{m}} - scales: {scale_string}""", end="")
                else:
                    # scales = ["""scale: {i}: {datarow[f"scale_{i:02}"]}"""]
                    print(f"""\r{counter:{m}} - scales: {scale_string}""", end="")

                if counter == max_values and max_values != None:
                    print("we are done here")
                    return

#board1
#con = Mux(device=f"ttyUSB0", uid="0120211005135155")

#board2
con = Mux(device=f"ttyUSB0", uid="0120211005135902")
#con.zero_all_scales()
con.to_influx(client=client)
#con.create_csv(max_values=20)
