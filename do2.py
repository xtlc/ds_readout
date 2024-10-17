from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import time, csv, re, argparse
from environs import Env
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
#from influxdb_client_3 import InfluxDBClient3, Point
from datetime import datetime, timezone
import os

# Initialize the environment
env = Env()

# Read the .env file
env.read_env()

# InfluxDB parameters
token = env("INFLUX_TOKEN")
org = "abaton_influx"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
bucket = env("BUCKET")

client = influxdb_client.InfluxDBClient(url=host, token=token, org=org)

class Mux:
    """
    output looks like this: [weights_1, weights_2, weights_3, weights_4, temp_1, temp_2, temp_3, temp_4]
    """
    def __init__(self, uid, device, number_of_scales, max_values, sleep_time=60):
        self.UID = uid
        self.DEVICE = device
        self.CR = "\x0D"
        self.create_port()
        self.SCALES = number_of_scales
        self.COUNTER = 0
        self.MAX_VALUES = max_values
        self.SLEEP = sleep_time
        #print(self.zero_all_scales())
        #print("all scales were zeroed ...")


    def create_port(self, ):
        if os.name == "nt":
            self.ser = Serial(port=f"""{self.DEVICE}""", 
                              baudrate=9600, 
                              bytesize=EIGHTBITS, 
                              parity=PARITY_NONE, 
                              stopbits=STOPBITS_ONE, 
                              timeout=0.2, 
                              xonxoff=False, 
                              rtscts=False, 
                              dsrdtr=False)
        else:
            self.ser = Serial(port=f"""/dev/{self.DEVICE}""", 
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
        for i in range(self.SCALES):
            self.zero_scale(channel=i)
        
    def get_revision(self):
        self.muxwrite(cmd="gr", pre="#")
        values = self.muxread()
        print(f"did this --> {values} <-- work?")
        return values.replace("#06", "")

    def view_output(self, scale_values):
        BOLD = "\033[1m"
        RED = "\033[31m"
        YELLOW = "\033[33m"
        CYAN = "\033[36m"
        BLUE = "\033[34m"
        RESET = "\033[0m"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        m = f"""0{len(str(self.MAX_VALUES))}"""
        out = f"""{self.COUNTER:{m}} / {self.MAX_VALUES:{m}} - scales: """
        if self.SCALES == 8:
            scale_string = "  |  ".join([f"""{BOLD}{RED}{key}:{RESET} {scale_values[key]}kg""" for key in scale_values.keys() if key not in ["mux", "timestamp"]])
        elif self.SCALES == 4:
            # Convert keys to a list for slicing
            keys_list = list(scale_values.keys())
            t = []
            for idx, key in enumerate(keys_list):
                if idx < 4:
                    t.append(f"""{BOLD}{RED}{key}:{RESET} {float(scale_values[key]):06.3f}kg""")
                else:
                    t.append(f"""{BOLD}{CYAN}{key}:{RESET} {float(scale_values[key]):06.2f}Â°C""")
            scale_string = "  |  ".join(t)
        else:
            print("just printing the output:", scale_values)


        print(f"""\r{out}{scale_string}""", end="")
        
        if self.COUNTER == self.MAX_VALUES:
            return

class Measurement:
    def __init__(self, device_temp_usb=None, device_scale_usb=None, scale_uid=None, number_of_scales=0, measurements=0, sleep_time=60, client=None, bucket=None, org=None):
        if device_scale_usb:
            self.scales = Mux(device=device_scale_usb, uid=scale_uid, number_of_scales=number_of_scales, max_values=measurements, sleep_time=sleep_time)
            self.number_of_scales = number_of_scales
        if device_temp_usb:
            self.temps = Temp(device=device_temp_usb)
        if client:
            self.client = client
            self.org = org
            self.bucket = bucket
        self.wait_time = sleep_time ## seconds


    def to_influx(self, db_name="teststand_1"):
        write_to_influx = self.client.write_api(write_options=SYNCHRONOUS)
        while True:
            now = datetime.utcnow().replace(microsecond=0)

            w = self.scales.get_all_weights()
            t = self.temps.get_all_temps()

            if self.number_of_scales == 1:
                print("we cannot do this for now")
                
            elif self.number_of_scales == 2:
                p_01 = influxdb_client.Point(db_name).field(f"scale_left", float(w["00"]) * 1000, ).time(now)
                p_02 = influxdb_client.Point(db_name).field(f"scale_right", float(w["01"]) * 1000, ).time(now)
                p_03 = influxdb_client.Point(db_name).field(f"temp_left_bot",  float(t[0]["temperature"])).time(now)
                p_04 = influxdb_client.Point(db_name).field(f"humid_left_bot", float(t[0]["humidity"])).time(now)
                p_05 = influxdb_client.Point(db_name).field(f"temp_left_top",  float(t[1]["temperature"])).time(now)
                p_06 = influxdb_client.Point(db_name).field(f"humid_left_top", float(t[1]["humidity"])).time(now)
                p_07 = influxdb_client.Point(db_name).field(f"temp_mid_bot",  float(t[2]["temperature"])).time(now)
                p_08 = influxdb_client.Point(db_name).field(f"humid_mid_bot", float(t[2]["humidity"])).time(now)
                p_09 = influxdb_client.Point(db_name).field(f"temp_mid_top", float(t[3]["temperature"])).time(now)
                p_10 = influxdb_client.Point(db_name).field(f"humid_mid_top",  float(t[3]["humidity"])).time(now)
                p_11 = influxdb_client.Point(db_name).field(f"temp_right_bot", float(t[4]["temperature"])).time(now)
                p_12 = influxdb_client.Point(db_name).field(f"humid_right_bot", float(t[4]["humidity"])).time(now)
                p_13 = influxdb_client.Point(db_name).field(f"temp_right_top", float(t[5]["temperature"])).time(now)
                p_14 = influxdb_client.Point(db_name).field(f"humid_right_top", float(t[5]["humidity"])).time(now)
                write_to_influx.write(bucket=self.bucket, record=[p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, p_12, p_13, p_14])
            time.sleep(self.wait_time)
            print("points written to influx: ", now)

    def to_terminal(self):
        while True:
            w = self.scales.get_all_weights()
            t = self.temps.get_all_temps()
            print("---> w -->", w)
            print("---> t -->", t)
            time.sleep(self.wait_time)

class Temp:
    def __init__(self, device, ):
        self.DEVICE = device
        self.create_port()
        self.CR = "\x0D"
        self.sensors = self.get_all_temps()
        print("available temp sensors:", self.sensors)
    
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
        tmp = readout.split(" ")
        return {"sensor": int(tmp[0]), "temp": float(tmp[1]), "humid": float(tmp[2])}


def check_args(args):
    def fmt_time(seconds, granularity=2):
        intervals = [("d", 86400),    # 60 * 60 * 24
                    ("h", 3600),    # 60 * 60
                    ("m", 60),
                    ("s", 1)]
        result = []
        for name, count in intervals:
            value = int(seconds // count)
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip("s")
                result.append(f"{value}{name}")
        t = " ".join(result[:granularity])
        return t + " s"

   # Use the USB device name, defaulting to ttyUSB0 if not provided
    usb_port = args.usb if args.usb else "ttyUSB0"

    if args.usb:
        print(f"trying to use {args.usb}")
        usb_port = args.usb
    else:
        print("using standard USB ttyUSB0")
        usb_port = "ttyUSB0"

    # a mux must be selected:
    if args.mux is None or args.mux not in mux_dict.keys():
        print("a valid mux must be chosen. Aborting!")
        exit()
    else:
        print(f"Choosing mux: {args.mux}")
        mux = args.mux

    if args.zero:
        print("Zeroing all scales.")
        zero = True
        return usb_port, mux, False, False, False, zero
    else:
        zero = False


    # Check if at least one of -n or -t is provided
    if args.measurements is None:
            measurements = 0
    else:
        try:
            measurements = args.measurements
        except Exception as E:
            print("Error with number of measurements -> could not process", E)
            exit()
    if args.granularity is None:
        print("Error: You must provide -g (granularity)")
        exit()  # Exit the script with a non-zero status
    else:
        try:
            granularity = int(args.granularity)
        except Exception as E:
            print("Error with number of measurements -> could not process", E)
            exit()
    
    if measurements > 0:
        print(f"{measurements} will be done, one every {granularity} seconds - this will take approx { fmt_time(measurements * granularity)}")
    else:
        print(f"measurements will be done continuosly, one every {granularity} seconds")

    
    # If no mutually exclusive options are provided, default to verbose
    if not (args.influx or args.csv):
        output_method = "terminal"
        print("Outputting values to terminal.")
    elif args.influx:
        print(f"Writing data continuously to InfluxDB into bucket {bucket}")
        output_method = "influx"
    elif args.csv:
        print(f"Writing data to CSV file")
        output_method = "csv"
    return usb_port, mux, output_method, measurements, granularity, zero

    
if __name__ == "__main__":
    mux_dict = {1: {"uid": "0120211005135155", "comment": "mux_4kg_1", "number_of_scales": 8}, 
                2: {"uid": "0120211005135902", "comment": "mux_4kg_2", "number_of_scales": 8},
                3: {"uid": "0020240425142741", "comment": "mux_8kg_1", "number_of_scales": 4},}

    # parser = argparse.ArgumentParser(description="Process some options.")

    # ## select where the script will show/save it"s data
    # group_save = parser.add_mutually_exclusive_group(required=False)
    # group_save.add_argument("-i", "--influx", action="store_true", help="Write data to InfluxDB")
    # group_save.add_argument("-c", "--csv", action="store_true", help="Write data to CSV")
    # group_save.add_argument("-v", "--verbose", action="store_true", help="Output values to terminal")

    # parser.add_argument("-n", "--measurements", type=int, help="Quit after n measurements, set 0 for continuos measurement")
    # parser.add_argument("-g", "--granularity", type=int, help="granularity - seconds between measurements")
    # parser.add_argument("-z", "--zero", action="store_true", help="Zero all scales")
    # parser.add_argument("-u", "--usb", type=str, help="Define USB in Linux device name (e.g., ttyUSB0)")
    # parser.add_argument("-m", "--mux", type=int, choices=mux_dict.keys(), help=f"Choose mux. Options are {mux_dict.keys()}")

    # args = parser.parse_args()

    # usb_port, mux, output_method, measurements, granularity, zero = check_args(args)
    # con = Mux(device=usb_port, uid=mux_dict[args.mux]["uid"], number_of_scales=mux_dict[args.mux]["number_of_scales"], max_values=measurements, sleep_time=granularity)


    # if not (rev := con.get_revision()):
    #     print("cannot take measurements - please check power supply and provided USB adapter settings, check cable integrity")
    #     exit()
    # else:
    #     print("scale revision:", rev)

    # if zero == True:
    #     con.zero_all_scales()
    #     print("done!")
    #     exit()
    
    # if output_method == "influx":
    #     m = Measurement(device_temp_usb="ttyUSB0", 
    #                     device_scale="ttyUSB1", 
    #                     scale_uid=mux_dict[args.mux]["uid"], 
    #                     number_of_scales=1, 
    #                     measurements=10, 
    #                     sleep_time=3, 
    #                     client=client)
    # elif output_method == "csv":
    #     con.to_csv()
    # else:
    #     con.to_terminal()
    # print("\n we are done!")

    m = Measurement(device_temp_usb="ttyUSB0", 
                    device_scale_usb="ttyUSB1", 
                    scale_uid="0020240425142741", 
                    number_of_scales=2, 
                    measurements=0, 
                    sleep_time=10, 
                    client=client,
                    org=org,
                    bucket=bucket).to_influx()
