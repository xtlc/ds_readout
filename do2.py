import time
from environs import Env
import influxdb_client import InfluxDBClient, Point 
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from scales import Mux
from ds210 import Temp
from flow import Flow

# Initialize the environment
env = Env()

# Read the .env file
env.read_env()

# InfluxDB parameters
token = env("INFLUX_TOKEN")
org = "abaton_influx"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
bucket = env("BUCKET")

client = InfluxDBClient(url=host, token=token, org=org)

class Measurement:
    def __init__(self, 
                 device_temp_usb=None,
                 device_flow_GPIO=None, 
                 device_scale_usb=None, 
                 scale_uid=None, 
                 number_of_scales=0, 
                 measurements=0, 
                 sleep_time=60, 
                 client=None, 
                 bucket=None, 
                 org=None):
        if device_scale_usb:
            self.scales = Mux(device=device_scale_usb, uid=scale_uid, number_of_scales=number_of_scales, max_values=measurements, sleep_time=sleep_time)
            self.number_of_scales = number_of_scales
        if device_temp_usb:
            self.temps = Temp(device=device_temp_usb)
        if device_flow_GPIO:
            self.flow = Flow(gpio=device_flow_GPIO)
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
                p_01 = Point(db_name).field(f"scale_left",      float(w["00"])              * 1000, ).time(now)
                p_02 = Point(db_name).field(f"scale_right",     float(w["01"])              * 1000, ).time(now)
                p_03 = Point(db_name).field(f"temp_left_bot",   float(t[0]["temperature"])          ).time(now)
                p_04 = Point(db_name).field(f"humid_left_bot",  float(t[0]["humidity"])             ).time(now)
                p_05 = Point(db_name).field(f"temp_left_top",   float(t[1]["temperature"])          ).time(now)
                p_06 = Point(db_name).field(f"humid_left_top",  float(t[1]["humidity"])             ).time(now)
                p_07 = Point(db_name).field(f"temp_mid_bot",    float(t[2]["temperature"])          ).time(now)
                p_08 = Point(db_name).field(f"humid_mid_bot",   float(t[2]["humidity"])             ).time(now)
                p_09 = Point(db_name).field(f"temp_mid_top",    float(t[3]["temperature"])          ).time(now)
                p_10 = Point(db_name).field(f"humid_mid_top",   float(t[3]["humidity"])             ).time(now)
                p_11 = Point(db_name).field(f"temp_right_bot",  float(t[4]["temperature"])          ).time(now)
                p_12 = Point(db_name).field(f"humid_right_bot", float(t[4]["humidity"])             ).time(now)
                p_13 = Point(db_name).field(f"temp_right_top",  float(t[5]["temperature"])          ).time(now)
                p_14 = Point(db_name).field(f"humid_right_top", float(t[5]["humidity"])             ).time(now)
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
    
if __name__ == "__main__":
    mux_dict = {1: {"uid": "0120211005135155", "comment": "mux_4kg_1", "number_of_scales": 8}, 
                2: {"uid": "0120211005135902", "comment": "mux_4kg_2", "number_of_scales": 8},
                3: {"uid": "0020240425142741", "comment": "mux_8kg_1", "number_of_scales": 4},}

    m = Measurement(device_temp_usb="ttyUSB0", 
                    device_scale_usb="ttyUSB1", 
                    scale_uid="0020240425142741", 
                    number_of_scales=2, 
                    measurements=0, 
                    sleep_time=10, 
                    client=client,
                    org=org,
                    bucket=bucket).to_influx()
