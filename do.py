from serial import Serial, EIGHTBITS, STOPBITS_ONE, PARITY_NONE
import time, csv, re, argparse
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
    def __init__(self, uid, device, number_of_scales, max_values, sleep_time=60):
        self.UID = uid
        self.DEVICE = device
        self.CR = "\x0D"
        self.create_port()
        self.SCALES = number_of_scales
        self.COUNTER = 0
        self.MAX_VALUES = max_values
        self.SLEEP = sleep_time

    def create_port(self, ):
        self.ser = Serial(port=f"""/dev/{self.DEVICE}""", baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=0.2, xonxoff=False, rtscts=False, dsrdtr=False)

    @staticmethod
    def calculate_crc(data):
        crc = 0
        for byte in data:
            crc ^= ord(byte)
        crc_hex = format(crc, "02x")
        return crc_hex

    def sanitize(self, mux_readout):
        # Regular expression to match the required pattern
        pattern = r"([-]?\d{5})\.(\d{3})"
        # Find all matches in the serial output
        matches = re.findall(pattern, mux_readout)

        ## sometimes more scales are returned than physically exist
        matches = matches[:self.SCALES]
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
        print("mux write:", cmd.encode("utf-8"))
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
        self.COUNTER += 1
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
        values = mux_readout=self.muxread()
        return values.replace("#06", "")

    def view_output(self, scale_values):
        BOLD = "\033[1m"
        RED = "\033[31m"
        RESET = "\033[0m"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        m = f"""0{len(str(self.MAX_VALUES))}"""
        out = f"""{self.COUNTER:{m}} / {self.MAX_VALUES:{m}} - scales: """
        scale_string = "  |  ".join([f"""{BOLD}{RED}{key}:{RESET} {scale_values[key]}kg""" for key in scale_values.keys() if key not in ["mux", "timestamp"]])
        print(f"""\r{out}{scale_string}""", end="")
        
        if self.COUNTER == self.MAX_VALUES:
            return

    def to_csv(self):
        csv_file_name = f"""log_from_{datetime.now().strftime("%Y-%m-%d___%H-%M-%S")}.csv"""
        
        print(f"""csv file {csv_file_name} is being written ...\n""")
        with open(csv_file_name, mode="w", newline="") as csvfile:
            fieldnames = ["mux", "timestamp", *[f"scale_{i:02}" for i in range(self.SCALES)]]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            while True:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                w = self.get_all_weights()
                datarow = {"mux": self.UID, "timestamp": now,  **{f"scale_{i:02}": w[f"{i:02}"] for i in range(self.SCALES)}}
                writer.writerow(datarow)
                self.view_output(scale_values=w)

                if self.COUNTER == self.MAX_VALUES:
                    return

    def to_influx(self, client, db_name="digisense_test_1"):
        while True:
            w = self.get_all_weights()
            self.view_output(scale_values=w)
            for scale, weight in w.items():
                p = Point(db_name).field(f"scale_{scale}", float(weight) * 1000).time(datetime.utcnow())
                client.write(record=p)

            if self.COUNTER == self.MAX_VALUES:
                return

    def to_terminal(self):
        while True:
            w = self.get_all_weights()
            self.view_output(scale_values=w)

            if self.COUNTER == self.MAX_VALUES:
                return


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
    if args.num_measurements is None and args.time is None:
        print("Error: You must provide either -n (number of measurements) or -t (time in minutes).")
        sys.exit(1)  # Exit the script with a non-zero status
    elif args.time is None:
        print(f"Quitting after {args.num_measurements} measurements.")
    elif args.num_measurements is None:
        print(f"Quitting after {args.time} minutes.")

    if args.granularity is None:
        measurements_interval = 1
    elif 0.01 < args.granularity < 12:
        measurements_interval = args.granularity
        print(f"measure interval was set to {measurements_interval} measures per minute")
    else:
        print("this interval cannot be used. please choose a value between 1 measurement per hour and 1 measurement every second")
        exit()  

    if args.num_measurements:
        predicted_time = args.num_measurements * measurements_interval
        num_measurements = args.num_measurements
    elif args.time:
        num_measurements = int(args.time * 1 / measurements_interval)
        predicted_time = args.time
    print(f"""{num_measurements} measurements will be done in {fmt_time(predicted_time)} - one measurement every {measurements_interval} seconds""")
    
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
    return usb_port, mux, output_method, measurements_interval, num_measurements, zero

    
if __name__ == "__main__":
    mux_dict = {1: {"uid": "0120211005135155", "comment": "mux_4kg_1", "number_of_scales": 8}, 
                2: {"uid": "0120211005135902", "comment": "mux_4kg_2", "number_of_scales": 8},
                3: {"uid": "0020240425142741", "comment": "mux_8kg_1", "number_of_scales": 4},}

    parser = argparse.ArgumentParser(description="Process some options.")

    ## select where the script will show/save it"s data
    group_save = parser.add_mutually_exclusive_group(required=False)
    group_save.add_argument("-i", "--influx", action="store_true", help="Write data continuously to InfluxDB")
    group_save.add_argument("-c", "--csv", action="store_true", help="Write data to CSV")
    group_save.add_argument("-v", "--verbose", action="store_true", help="Output values to terminal")

    ## define how many or how long the script will run
    group_number = parser.add_mutually_exclusive_group(required=False)
    group_number.add_argument("-n", "--num_measurements", type=int, help="Quit after n measurements")
    group_number.add_argument("-t", "--time", type=int, help="Quit after t minutes")

    parser.add_argument("-z", "--zero", action="store_true", help="Zero all scales")
    parser.add_argument("-g", "--granularity", type=float, help="granularity - how often in one minute should be measured?")
    parser.add_argument("-u", "--usb", type=str, help="Define USB in Linux device name (e.g., ttyUSB0)")
    parser.add_argument("-m", "--mux", type=int, choices=mux_dict.keys(), help=f"Choose mux. Options are {mux_dict.keys()}")

    args = parser.parse_args()


    usb_port, mux, output_method, measurements_interval, num_measurements, zero = check_args(args)
    con = Mux(device=usb_port, uid=mux_dict[args.mux]["uid"], number_of_scales=mux_dict[args.mux]["number_of_scales"], max_values=num_measurements, sleep_time=measurements_interval)


    if not (rev := con.get_revision()):
        print("cannot take measurements - please check power supply and provided USB adapter settings, check cable integrity")
        exit()
    else:
        print("scale revision:", rev)

    if zero == True:
        con.zero_all_scales()
        print("done!")
        exit()
    
    if output_method == "influx":
        con.to_influx(client=client)
    elif output_method == "csv":
        con.to_csv()
    else:
        con.to_terminal()
    print("\n we are done!")