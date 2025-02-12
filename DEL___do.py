import time, csv, re, argparse, os
from environs import Env
from influxdb_client_3 import InfluxDBClient3, Point
from datetime import datetime, timezone
import RPi.GPIO as GPIO
from scales import Mux
from ens210 import Temp


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


class Measurement:
    def __init__(self, device_temp_usb=None, device_scale_usb=None, scale_uid=None, number_of_scales=0, measurements=0, sleep_time=60, client=None):
        if device_scale_usb:
            self.scales = Mux(device=device_scale_usb, uid=scale_uid, number_of_scales=number_of_scales, max_values=measurements, sleep_time=sleep_time)
            self.number_of_scales = number_of_scales
        if device_temp_usb:
            self.temps = Temp(device=device_temp_usb)
        if client:
            self.client = client
        self.wait_time = sleep_time ## seconds

    def to_csv(self):
        csv_file_name = f"""log_from_{datetime.now().strftime("%Y-%m-%d___%H-%M-%S")}.csv"""
        with open(csv_file_name, mode="w", newline="") as csvfile:
            w = self.scales.get_all_weights()
            t = self.temps.get_all_temps()
            scales = ["mux", "timestamp", *[f"scale_{i:02}" for i in range(self.SCALES)]]
            temps = self.temps

    # def to_csv(self):
    #     csv_file_name = f"""log_from_{datetime.now().strftime("%Y-%m-%d___%H-%M-%S")}.csv"""
        
    #     print(f"""csv file {csv_file_name} is being written ...\n""")
    #     with open(csv_file_name, mode="w", newline="") as csvfile:
    #         fieldnames = ["mux", "timestamp", *[f"scale_{i:02}" for i in range(self.SCALES)]]
    #         writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
    #         writer.writeheader()
    #         while True:
    #             now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #             w = self.get_all_weights()
    #             datarow = {"mux": self.UID, "timestamp": now,  **{f"scale_{i:02}": w[f"{i:02}"] for i in range(self.SCALES)}}
    #             writer.writerow(datarow)
    #             self.view_output(scale_values=w)

    def to_influx(self, db_name="teststand_1"):
        while True:
            w = self.scales.get_all_weights()
            t = self.temps.get_all_temps()
            time.sleep(self.wait_time)
            #for scale, weight in w.items():
            #    p = Point(db_name).field(f"scale_{scale}", float(weight) * 1000).time(datetime.utcnow())
            #    client.write(record=p)

            if self.number_of_scales == 1:
                now = datetime.utcnow()
                ## add mux id here?
                p_01 = Point(db_name).field(f"scale_1", float(w["00"]) * 1000, ).time(now)
                client.write(record=p_01)
                p_02 = Point(db_name).field(f"temp_left_bot",  float(t[0]["temperature"])).time(now)
                client.write(record=p_02)
                p_03 = Point(db_name).field(f"humid_left_bot", float(t[0]["humidity"])).time(now)
                client.write(record=p_03)
                p_04 = Point(db_name).field(f"temp_left_top",  float(t[1]["temperature"])).time(now)
                client.write(record=p_04)
                p_05 = Point(db_name).field(f"humid_left_top", float(t[1]["humidity"])).time(now)
                client.write(record=p_05)
                p_06 = Point(db_name).field(f"temp_mid_bot",  float(t[2]["temperature"])).time(now)
                client.write(record=p_06)
                p_07 = Point(db_name).field(f"humid_mid_bot", float(t[2]["humidity"])).time(now)
                client.write(record=p_07)
                p_08 = Point(db_name).field(f"temp_mid_top", float(t[3]["temperature"])).time(now)
                client.write(record=p_08)
                p_09 = Point(db_name).field(f"humi_mid_top",  float(t[3]["humidity"])).time(now)
                client.write(record=p_09)
                p_10 = Point(db_name).field(f"temp_right_bot", float(t[4]["temperature"])).time(now)
                client.write(record=p_10)
                p_11 = Point(db_name).field(f"humid_right_bot", float(t[4]["humidity"])).time(now)
                client.write(record=p_11)
                p_12 = Point(db_name).field(f"temp_right_top", float(t[5]["temperature"])).time(now)
                client.write(record=p_12)
                p_13 = Point(db_name).field(f"humid_right_top", float(t[5]["humidity"])).time(now)
                client.write(record=p_13)
                print("points written to influx: ", now)

    def to_terminal(self):
        while True:
            w = self.scales.get_all_weights()
            t = self.temps.get_all_temps()
            print("---> w -->", w)
            print("---> t -->", t)
            time.sleep(self.wait_time)



class Flow:
    def __init__(self, FLOW_SENSOR_GPIO=13):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FLOW_SENSOR_GPIO, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.gpio
        self.count = 0

    def countPulse(self, channel):
        if self.start_counter == 1:
            self.count = self.count+1

    def get_flow(self):
        GPIO.add_event_detect(self.gpio, GPIO.FALLING, callback=self.countPulse)
        while True:
            self.start_counter = 1
            time.sleep(1)
            self.start_counter = 0
            flow = (self.count/23)
            print("The flow is: %.3f Liter/min" % (flow))
            self.count = 0
            time.sleep(5)




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
                    number_of_scales=1, 
                    measurements=10, 
                    sleep_time=3, 
                    client=client).to_influx()



+sort(Stock!C1:C; NICHT(ISTLEER(Stock!C1:C)) * ZEILE(Stock!C1:C); FALSCH)
+sort(Stock!D1:D; NICHT(ISTLEER(Stock!D1:D)) * ZEILE(Stock!D1:D); FALSCH)
+sort(Stock!E1:E; NICHT(ISTLEER(Stock!E1:E)) * ZEILE(Stock!E1:E); FALSCH)
+sort(Stock!F1:F; NICHT(ISTLEER(Stock!F1:F)) * ZEILE(Stock!F1:F); FALSCH)
+sort(Stock!G1:G; NICHT(ISTLEER(Stock!G1:G)) * ZEILE(Stock!G1:G); FALSCH)
+sort(Stock!H1:H; NICHT(ISTLEER(Stock!H1:H)) * ZEILE(Stock!H1:H); FALSCH)
+sort(Stock!I1:I; NICHT(ISTLEER(Stock!I1:I)) * ZEILE(Stock!I1:I); FALSCH)
+sort(Stock!J1:J; NICHT(ISTLEER(Stock!J1:J)) * ZEILE(Stock!J1:J); FALSCH)
+sort(Stock!K1:K; NICHT(ISTLEER(Stock!K1:K)) * ZEILE(Stock!K1:K); FALSCH)
+sort(Stock!L1:L; NICHT(ISTLEER(Stock!L1:L)) * ZEILE(Stock!L1:L); FALSCH)
+sort(Stock!M1:M; NICHT(ISTLEER(Stock!M1:M)) * ZEILE(Stock!M1:M); FALSCH)
+sort(Stock!P1:P; NICHT(ISTLEER(Stock!P1:P)) * ZEILE(Stock!P1:P); FALSCH)

1001 D
=GANZZAHL(min(
    +sort(Stock!C1:C; NICHT(ISTLEER(Stock!C1:C)) * ZEILE(Stock!C1:C); FALSCH);
    +sort(Stock!D1:D; NICHT(ISTLEER(Stock!D1:D)) * ZEILE(Stock!D1:D); FALSCH);
    +sort(Stock!H1:H; NICHT(ISTLEER(Stock!H1:H)) * ZEILE(Stock!H1:H); FALSCH)/B10; 
    +sort(Stock!J1:J; NICHT(ISTLEER(Stock!J1:J)) * ZEILE(Stock!J1:J); FALSCH)/B12;
    +sort(Stock!K1:K; NICHT(ISTLEER(Stock!K1:K)) * ZEILE(Stock!K1:K); FALSCH)/B13;
    +sort(Stock!L1:L; NICHT(ISTLEER(Stock!L1:L)) * ZEILE(Stock!L1:L); FALSCH)/B20;
    +sort(Stock!M1:M; NICHT(ISTLEER(Stock!M1:M)) * ZEILE(Stock!M1:M); FALSCH);
    +sort(Stock!P1:P; NICHT(ISTLEER(Stock!P1:P)) * ZEILE(Stock!P1:P); FALSCH)
))

1002 E
=GANZZAHL(min(
    +sort(Stock!C1:C; NICHT(ISTLEER(Stock!C1:C)) * ZEILE(Stock!C1:C); FALSCH);
    +sort(Stock!E1:E; NICHT(ISTLEER(Stock!E1:E)) * ZEILE(Stock!E1:E); FALSCH);
    +sort(Stock!H1:H; NICHT(ISTLEER(Stock!H1:H)) * ZEILE(Stock!H1:H); FALSCH)/B10; 
    +sort(Stock!J1:J; NICHT(ISTLEER(Stock!J1:J)) * ZEILE(Stock!J1:J); FALSCH)/B12;
    +sort(Stock!K1:K; NICHT(ISTLEER(Stock!K1:K)) * ZEILE(Stock!K1:K); FALSCH)/B13;
    +sort(Stock!L1:L; NICHT(ISTLEER(Stock!L1:L)) * ZEILE(Stock!L1:L); FALSCH)/B20;
    +sort(Stock!M1:M; NICHT(ISTLEER(Stock!M1:M)) * ZEILE(Stock!M1:M); FALSCH);
    +sort(Stock!P1:P; NICHT(ISTLEER(Stock!P1:P)) * ZEILE(Stock!P1:P); FALSCH)
))

1003 F
=GANZZAHL(min(
    +sort(Stock!C1:C; NICHT(ISTLEER(Stock!C1:C)) * ZEILE(Stock!C1:C); FALSCH);
    +sort(Stock!F1:F; NICHT(ISTLEER(Stock!F1:F)) * ZEILE(Stock!F1:F); FALSCH);
    +sort(Stock!H1:H; NICHT(ISTLEER(Stock!H1:H)) * ZEILE(Stock!H1:H); FALSCH)/B10; 
    +sort(Stock!J1:J; NICHT(ISTLEER(Stock!J1:J)) * ZEILE(Stock!J1:J); FALSCH)/B12;
    +sort(Stock!K1:K; NICHT(ISTLEER(Stock!K1:K)) * ZEILE(Stock!K1:K); FALSCH)/B13;
    +sort(Stock!L1:L; NICHT(ISTLEER(Stock!L1:L)) * ZEILE(Stock!L1:L); FALSCH)/B20;
    +sort(Stock!M1:M; NICHT(ISTLEER(Stock!M1:M)) * ZEILE(Stock!M1:M); FALSCH);
    +sort(Stock!P1:P; NICHT(ISTLEER(Stock!P1:P)) * ZEILE(Stock!P1:P); FALSCH)
))

1004 G
=GANZZAHL(min(
    +sort(Stock!C1:C; NICHT(ISTLEER(Stock!C1:C)) * ZEILE(Stock!C1:C); FALSCH);
    +sort(Stock!G1:G; NICHT(ISTLEER(Stock!G1:G)) * ZEILE(Stock!G1:G); FALSCH);
    +sort(Stock!H1:H; NICHT(ISTLEER(Stock!H1:H)) * ZEILE(Stock!H1:H); FALSCH)/B10; 
    +sort(Stock!J1:J; NICHT(ISTLEER(Stock!J1:J)) * ZEILE(Stock!J1:J); FALSCH)/B12;
    +sort(Stock!K1:K; NICHT(ISTLEER(Stock!K1:K)) * ZEILE(Stock!K1:K); FALSCH)/B13;
    +sort(Stock!L1:L; NICHT(ISTLEER(Stock!L1:L)) * ZEILE(Stock!L1:L); FALSCH)/B20;
    +sort(Stock!M1:M; NICHT(ISTLEER(Stock!M1:M)) * ZEILE(Stock!M1:M); FALSCH);
    +sort(Stock!P1:P; NICHT(ISTLEER(Stock!P1:P)) * ZEILE(Stock!P1:P); FALSCH)
))

1005
=GANZZAHL(min(
    +sort(Stock!C1:C; NICHT(ISTLEER(Stock!C1:C)) * ZEILE(Stock!C1:C); FALSCH);
    +sort(Stock!F1:F; NICHT(ISTLEER(Stock!F1:F)) * ZEILE(Stock!F1:F); FALSCH);
    +sort(Stock!H1:H; NICHT(ISTLEER(Stock!H1:H)) * ZEILE(Stock!H1:H); FALSCH)/B10; 
    +sort(Stock!J1:J; NICHT(ISTLEER(Stock!J1:J)) * ZEILE(Stock!J1:J); FALSCH)/B12;
    +sort(Stock!K1:K; NICHT(ISTLEER(Stock!K1:K)) * ZEILE(Stock!K1:K); FALSCH)/B13;
    +sort(Stock!L1:L; NICHT(ISTLEER(Stock!L1:L)) * ZEILE(Stock!L1:L); FALSCH)/B20;
    +sort(Stock!M1:M; NICHT(ISTLEER(Stock!M1:M)) * ZEILE(Stock!M1:M); FALSCH);
    +sort(Stock!P1:P; NICHT(ISTLEER(Stock!P1:P)) * ZEILE(Stock!P1:P); FALSCH)
))