import time
from environs import Env
from influxdb_client import InfluxDBClient, Point 
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from scales import Mux
from ds210 import Temp
from flow import Flow
from cam import Cam
import colorama
from colorama import Fore, Style

# Initialize the environment & read env file
env = Env()
env.read_env()

# InfluxDB parameters
token = env("INFLUX_TOKEN")
org = "abaton_influx"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
bucket = env("BUCKET")

class Measurement:
    def __init__(self, 
                 device_temp_usb=None,
                 device_flow_GPIOs=None, 
                 device_scale_usb=None, 
                 scale_uid=None, 
                 number_of_scales=0, 
                 measurements=0, 
                 sleep_time=60, 
                 host=None,
                 token=None,
                 bucket=None, 
                 cam=False,
                 org=None):
        if device_scale_usb:
            self.scales = Mux(device=device_scale_usb, uid=scale_uid, number_of_scales=number_of_scales, max_values=measurements, sleep_time=sleep_time)
            self.number_of_scales = number_of_scales
        if device_temp_usb:
            self.temps = Temp(device=device_temp_usb)
        if device_flow_GPIOs:
            self.flow = Flow(FLOW_SENSOR_GPIO_RIGHT=device_flow_GPIOs[0], FLOW_SENSOR_GPIO_LEFT=device_flow_GPIOs[1],)
        if cam:
            self.cam = Cam(resolution=[1920, 1080], filetype="jpeg")
        if host:
            self.client = InfluxDBClient(url=host, token=token, org=org)
            self.bucket = bucket
        self.wait_time = sleep_time ## seconds

        # Initialize colorama
        colorama.init()


    def to_influx(self, db_name="teststand_1"):
        print("start writing to influx ...")
        write_to_influx = self.client.write_api(write_options=SYNCHRONOUS)
        while True:
            now = datetime.utcnow().replace(microsecond=0)

            w = self.scales.get_all_weights()
            t = self.temps.get_all_temps()
            f = self.flow.get_flow()
            if hasattr(self, "cam"):
                self.cam.shoot(filename=now.strftime("%Y_%m_%d__%H_%M_%S"))

            if self.number_of_scales  == 2:
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
                p_15 = Point(db_name).field(f"flow_left",       float(f["flow_left"])               ).time(now)
                p_16 = Point(db_name).field(f"flow_right",      float(f["flow_right"])              ).time(now)
                write_to_influx.write(bucket=self.bucket, record=[p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, p_12, p_13, p_14, p_15, p_16])
            else:
                print(f"number of scales not supported: {self.number_of_scales}")
                exit()
            self.to_terminal(w=w, t=t, f=f)
            time.sleep(self.wait_time)

    def to_terminal(self, w=None, f=None, t=None):
        def my_format(v):
            total_width = 10
            if isinstance(v, str):
                x = v.lstrip("0")
                if x.startswith("."):
                    x = f"0{x}"
                leading_spaces = total_width - len(x)
                formatted_value = " " * leading_spaces + x
            else:
                formatted_value = f"""{v:>{total_width}.3f}"""
            return f"""{formatted_value}"""

        if self.number_of_scales == 2:
            head = "scale_left | scale_right | \033[31mt_left_top\033[39m | \033[31mt_left_bot\033[39m | \033[31mt_mid_top\033[39m  | \033[31mt_mid_bot\033[39m  | \033[31mt_right_top\033[39m | \033[31mt_right_bot\033[39m "
            head += "| h_left_top | h_left_bot | h_mid_top  | h_mid_bot | h_right_top | h_right_bot | flow_left | flow_right |\n"
            head += "------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"
            
            counter = 0
            while True:
                if counter % 10 == 0:
                    print(head)
                out = ""
                if hasattr(self, "scales"):
                    if w == None: 
                        w = self.scales.get_all_weights()
                    out += f"""{my_format(w["00"])} |  {my_format(w["01"])} | """

                if hasattr(self, "temps"):
                    if t == None:
                        t = self.temps.get_all_temps()
                    out += f"""\033[31m{my_format(t[1]["temperature"])}\033[39m | \033[31m{my_format(t[0]["temperature"])}\033[39m | \033[31m{my_format(t[3]["temperature"])}\033[39m | \033[31m{my_format(t[2]["temperature"])}\033[39m |  \033[31m{my_format(t[5]["temperature"])}\033[39m |  \033[31m{my_format(t[4]["temperature"])}\033[39m | """
                    out += f"""{my_format(t[1]["humidity"])} | {my_format(t[0]["humidity"])} | {my_format(t[3]["humidity"])} | {my_format(t[2]["humidity"])} | {my_format(t[5]["humidity"])} | {my_format(t[4]["humidity"])} | """

                if hasattr(self, "flow"):
                    if f == None:
                        f = self.flow.get_flow()
                    out += f"""{my_format(f["flow_left"])} | {my_format(f["flow_right"])} | """

                print(out)
                counter += 1
                time.sleep(self.wait_time)
        
if __name__ == "__main__":
    mux_dict = {1: {"uid": "0120211005135155", "comment": "mux_4kg_1", "number_of_scales": 8}, 
                2: {"uid": "0120211005135902", "comment": "mux_4kg_2", "number_of_scales": 8},
                3: {"uid": "0020240425142741", "comment": "mux_8kg_1", "number_of_scales": 4},}

    m = Measurement(device_temp_usb="ttyUSB0", 
                    device_scale_usb="ttyUSB1", 
                    scale_uid="0020240425142741", 
                    device_flow_GPIOs=[12, 13],
                    number_of_scales=2, 
                    measurements=0, 
                    sleep_time=10, 
                    host=host,
                    token=token,
                    bucket=bucket,
                    org=org,
                    cam=False)
    #m.to_terminal()
    m.to_influx()