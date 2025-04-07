import time
from influxdb_client import InfluxDBClient, Point 
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from scales import Mux
from ens210 import Temp
from pt100 import PT100
from flow import Flow
import colorama
from environs import Env


class Measurement:
    def __init__(self, 
                 name_left=None,
                 name_right=None,
                 measurements=0, 
                 sleep_time=60, 
                 cam=False,
                 ircam=False,
                 foldername="rclone"):

        # Initialize the environment & read env file
        env = Env()
        env.read_env()

        # InfluxDB parameters
        self.token = env("INFLUX_TOKEN")
        self.org = "abaton_influx"
        self.host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
        self.host = "127.0.0.1:8186"
        self.bucket = env("BUCKET")
        self.client = InfluxDBClient(url=self.host, token=self.token, org=self.org)

        if name_left:
            self.scale_left = name_left
        else:
            self.scale_left = "scale_left"
        if name_right:
            self.scale_right = name_right
        else:
            self.scale_right = "scale_right"

        try:
            self.scales = Mux(max_values=measurements, sleep_time=sleep_time)
        except Exception as E:
            print(f"scales could not be initialized, aborting")
            exit()
        
        self.flows = Flow()
        self.pt100s = PT100()
        self.temps = Temp()

        if env("CAM") == 1:
            from cam import Cam
            self.cam = Cam(resolution=[1920, 1080], filetype="jpeg", foldername=foldername)

        if env("IRCAM") == 1:
            from ir import IRCam
            self.ircam = IRCam(foldername=foldername, name_left=name_left, name_right=name_right)

        self.wait_time = sleep_time ## seconds
        
        ## for rclone
        self.foldername = foldername

        # initialize tests:
        self.test()

        # Initialize colorama
        colorama.init()

    def test(self):
        print("starting up with some tests ...")
       
        w = self.scales.get_all_weights()
        print(f"""Values from the scales: {w}""")
        
        t = self.temps.get_all_temps()
        print(f"""Values from the ens210: {t}""")
        if len(t) != 12: 
            print(f"only {len(t)} temp/humidty/ens210 sensors were found - aborting!")
            exit()
        
        f = self.flows.get_flow()
        print(f"""Values from the flow sensors: {f}""")
        
        p = self.pt100s.get_temps()
        print(f"""Values from the pt100s: {p}""")
        
        print("all tests done.")
  
    def to_influx(self, db_name):
        print("start writing to influx ...")
        write_to_influx = self.client.write_api(write_options=SYNCHRONOUS)
        counter = 0
        while True:
            now = datetime.utcnow().replace(microsecond=0)
            
            if hasattr(self, "scales"):
                w = self.scales.get_all_weights()
            if hasattr(self, "ens210s"):
                t = self.temps.get_all_temps()
            if hasattr(self, "flows"):
                f = self.flows.get_flow()
            if hasattr(self, "pt100s"):
                p = self.pt100s.get_temps()
            if hasattr(self, "ircam"):
                self.ircam.save_image()
            if hasattr(self, "cam"):
                self.cam.shoot(filename=now.strftime("%Y_%m_%d__%H_%M_%S"))

            ## scale values
            try:
                p_01 = Point(db_name).field(f"{self.scale_left}_left", float(w["00"]) * 1000, ).time(now)
            except IndexError as E:
                p_01 = Point(db_name).field(f"{self.scale_left}_left", float('nan')).time(now)
            try:
                p_02 = Point(db_name).field(f"{self.scale_right}_right", float(w["01"]) * 1000, ).time(now)
            except IndexError as E:
                p_02 = Point(db_name).field(f"{self.scale_right}_right", float('nan')).time(now)
            
            ## temperature values
            p_03 = Point(db_name).field(f"temp_scale_left_bot", t["temp_bot_left"]).time(now)
            p_04 = Point(db_name).field(f"humid_scale_left_bot", t["humid_bot_left"]).time(now)
            p_05 = Point(db_name).field(f"temp_scale_left_top", t["temp_top_left"]).time(now)
            p_06 = Point(db_name).field(f"humid_scale_left_top", t["humid_top_left"]).time(now)
            p_07 = Point(db_name).field(f"temp_mid_bot", t["temp_bot_mid"]).time(now)
            p_08 = Point(db_name).field(f"humid_mid_bot", t["humid_bot_mid"]).time(now)
            p_09 = Point(db_name).field(f"temp_mid_top", t["temp_top_mid"]).time(now)
            p_10 = Point(db_name).field(f"humid_mid_top", t["humid_top_mid"]).time(now)
            p_11 = Point(db_name).field(f"temp_scale_right_bot", t["temp_bot_right"]).time(now)
            p_12 = Point(db_name).field(f"humid_scale_right_bot", t["humid_bot_right"]).time(now)
            p_13 = Point(db_name).field(f"temp_scale_right_top", t["temp_top_right"]).time(now)
            p_14 = Point(db_name).field(f"humid_scale_right_top", t["humid_top_right"]).time(now)
            
            ## flow values
            p_15 = Point(db_name).field(f"flow_left", float(f["flow_left"])).time(now)
            p_16 = Point(db_name).field(f"flow_right", float(f["flow_right"])).time(now)
             
            ## pt100 values
            p_17 = Point(db_name).field(f"water_temp_right_in",  float(p["in_ri"])).time(now)
            p_18 = Point(db_name).field(f"water_temp_right_out", float(p["out_ri"])).time(now)
            p_19 = Point(db_name).field(f"water_temp_left_in", float(p["in_le"])).time(now)
            p_20 = Point(db_name).field(f"water_temp_left_out", float(p["out_le"])).time(now)
           
            records = [p_01, p_02, p_03, p_04, p_05, p_06, p_07, p_08, p_09, p_10, p_11, p_12, p_13, p_14, p_15, p_16, p_17, p_18, p_19, p_20]
            
            try:
                write_to_influx.write(bucket=self.bucket, record=records)
            except Exception as E:
                print("caught an exception on connecting with influx ... waiting 3s and trying again")
                time.sleep(3)
                write_to_influx.write(bucket=self.bucket, record=records)
                print("now we succeded ...")

            self.print_to_terminal(counter=counter, w=w, t=t, f=f, p=p)
            counter += 1
            time.sleep(self.wait_time)

    def print_to_terminal(self, counter=None, w=None, f=None, t=None,p=None):
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

        head = f"\n\033[33mw_{self.scale_left}\033[39m | \033[33mw_{self.scale_right}\033[39m | \033[31mt_{self.scale_left}_top\033[39m | \033[31mt_{self.scale_left}_bot\033[39m | \033[31mt_mid_top\033[39m  | \033[31mt_mid_bot\033[39m  | \033[31mt_{self.scale_right}_top\033[39m | \033[31mt_{self.scale_right}_bot\033[39m "
        head += f"| \033[36mh_{self.scale_left}_top\033[39m | \033[36mh_{self.scale_left}_bot\033[39m | \033[36mh_mid_top\033[39m  | \033[36mh_mid_bot\033[39m | \033[36mh_{self.scale_right}_top\033[39m | \033[36mh_{self.scale_right}_bot\033[39m | \033[35mflow_{self.scale_left}\033[39m | \033[35mflow_{self.scale_right}\033[39m | "
        head += f"\033[93mwtr_in_{self.scale_left}\033[39m | \033[93mwtr_out_{self.scale_left}\033[39m | \033[93mwtr_in_{self.scale_right}\033[39m | \033[93mwtr_out_{self.scale_right}\033[39m | \n"
        head += f"-" * 276
        
        print(t)

        if counter % 10 == 0:
            print(head)
        out = ""
        out += f"""\033[33m{my_format(w["00"])}\033[39m |  \033[33m{my_format(w["01"])}\033[36m | """

        out += f"""\033[31m{my_format(t["temp_top_left"])}\033[39m | \033[31m{my_format(t["temp_bot_left"])}\033[39m | \033[31m{my_format(t["temp_top_mid"])}\033[39m | \033[31m{my_format(t["temp_bot_mid"])}\033[39m |  \033[31m{my_format(t["temp_top_right"])}\033[39m |  \033[31m{my_format(t["temp_bot_right"])}\033[39m | """
        out += f"""\033[36m{my_format(t["humid_top_left"])}\033[39m | \033[36m{my_format(t["humid_bot_left"])}\033[39m | \033[36m{my_format(t["humid_bot_mid"])}\033[39m | \033[36m{my_format(t["humid_bot_mid"])}\033[39m | \033[36m{my_format(t["humid_top_right"])}\033[39m | \033[36m{my_format(t["humid_bot_right"])}\033[39m | """

        out += f"""\033[35m{my_format(f["flow_left"])}\033[39m | \033[35m{my_format(f["flow_right"])}\033[39m | """
        out += f"""\033[93m{my_format(p["in_le"])}\033[39m | \033[93m{my_format(p["out_le"])}\033[39m | \033[93m{my_format(p["in_ri"])}\033[39m | \033[93m{my_format(p["out_ri"])}\033[39m |"""
        print(out)

    def to_terminal(self):
        counter = 0
        while True:
            if hasattr(self, "scales"):
                w = self.scales.get_all_weights()
            else:
                w = None
                
            if hasattr(self, "temps"):
                t = self.temps.get_all_temps()
            else:
                t = None
                
            if hasattr(self, "flows"):
                f = self.flows.get_flow()
            else:
                f = None
                
            if hasattr(self, "pt100s"): 
                p = self.pt100s.get_temps()   
            else:
                p = None

            self.print_to_terminal(counter=counter, w=w, t=t, f=f, p=p)
            counter += 1
            time.sleep(self.wait_time)
