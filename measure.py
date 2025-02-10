import time
from influxdb_client import InfluxDBClient, Point 
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from scales import Mux
from ens210 import Temp
from pt100 import PT100
from flow import Flow
from cam import Cam
from ir import IRCam
import colorama

class Measurement:
    def __init__(self, 
                 device_temp_usb=None,
                 device_flow_GPIOs=None, 
                 device_scale_usb=None, 
                 pt100s=None,
                 scale_uid=None, 
                 number_of_scales=0, 
                 measurements=0, 
                 sleep_time=60, 
                 host=None,
                 token=None,
                 bucket=None, 
                 cam=False,
                 ircam=False,
                 org=None):
        if device_scale_usb:
            self.scales = Mux(device=device_scale_usb, uid=scale_uid, number_of_scales=number_of_scales, max_values=measurements, sleep_time=sleep_time)
            self.number_of_scales = number_of_scales
        
        if device_temp_usb:
            self.temps = Temp(device=device_temp_usb)
        
        if device_flow_GPIOs:
            self.flow = Flow(FLOW_SENSOR_GPIO_RIGHT=device_flow_GPIOs[0], FLOW_SENSOR_GPIO_LEFT=device_flow_GPIOs[1],)
        
        if pt100s != None:
            self.pt100s = PT100(PT100_WATER_IN_RIGHT=pt100s["in_ri"], PT100_WATER_OUT_RIGHT=pt100s["out_ri"], PT100_WATER_IN_LEFT=pt100s["in_le"], PT100_WATER_OUT_LEFT=pt100s["out_le"])
        
        if cam:
            self.cam = Cam(resolution=[1920, 1080], filetype="jpeg")

        if ircam:
            self.ircam = IRCam()
        
        if host:
            self.client = InfluxDBClient(url=host, token=token, org=org)
            self.bucket = bucket
        self.wait_time = sleep_time ## seconds

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
        if len(t) != 6: 
            print(f"only {len(t)} temp/humidty/ens210 sensors were found - aborting!")
            exit()
        
        f = self.flow.get_flow()
        print(f"""Values from the flow sensors: {f}""")
        
        p = self.pt100s.get_temps()
        print(f"""Values from the pt100s: {p}""")
        
        print("all tests done.")


    def to_influx(self, db_name="teststand_1"):
        print("start writing to influx ...")
        write_to_influx = self.client.write_api(write_options=SYNCHRONOUS)
        counter = 0
        while True:
            now = datetime.utcnow().replace(microsecond=0)

            w = self.scales.get_all_weights()
            t = self.temps.get_all_temps()
            f = self.flow.get_flow()
            p = self.pt100s.get_temps()
            if hasattr(self, "ircam"):
                self.ircam.save_image()
            if hasattr(self, "cam"):
                self.cam.shoot(filename=now.strftime("%Y_%m_%d__%H_%M_%S"))

            ## scale values
            try:
                p_01 = Point(db_name).field(f"scale_left", float(w["00"]) * 1000, ).time(now)
            except IndexError as E:
                p_01 = Point(db_name).field(f"scale_left", float('nan')).time(now)
            try:
                p_02 = Point(db_name).field(f"scale_right", float(w["01"]) * 1000, ).time(now)
            except IndexError as E:
                p_02 = Point(db_name).field(f"scale_right", float('nan')).time(now)
            
            ## temperature values
            try:
                p_03 = Point(db_name).field(f"temp_left_bot", float(t[0]["temperature"])).time(now)
            except IndexError as E:
                p_04 = Point(db_name).field(f"temp_left_bot", float('nan')).time(now)
            try:
                p_04 = Point(db_name).field(f"humid_left_bot", float(t[0]["humidity"])).time(now)
            except IndexError as E:
                p_04 = Point(db_name).field(f"humid_left_bot", float('nan')).time(now)
            
            try:
                p_05 = Point(db_name).field(f"temp_left_top", float(t[1]["temperature"])).time(now)
            except IndexError as E:
                p_05 = Point(db_name).field(f"temp_left_top", float('nan')).time(now)
            try:
                p_06 = Point(db_name).field(f"humid_left_top", float(t[1]["humidity"])).time(now)
            except IndexError as E:
                p_06 = Point(db_name).field(f"humid_left_top", float('nan')).time(now)

            try:
                p_07 = Point(db_name).field(f"temp_mid_bot", float(t[2]["temperature"])).time(now)
            except IndexError as E:
                p_07 = Point(db_name).field(f"temp_mid_bot", float('nan')).time(now)
            try:
                p_08 = Point(db_name).field(f"humid_mid_bot", float(t[2]["humidity"])).time(now)
            except IndexError as E:
                p_08 = Point(db_name).field(f"humid_mid_bot", float('nan')).time(now)
            
            try:
                p_09 = Point(db_name).field(f"temp_mid_top", float(t[3]["temperature"])).time(now)
            except IndexError as E:
                p_09 = Point(db_name).field(f"temp_mid_top", float('nan')).time(now)
            try:
                p_10 = Point(db_name).field(f"humid_mid_top", float(t[3]["humidity"])).time(now)
            except IndexError as E:
                p_10 = Point(db_name).field(f"humid_mid_top", float('nan')).time(now)
            
            try:
                p_11 = Point(db_name).field(f"temp_right_bot", float(t[4]["temperature"])).time(now)
            except IndexError as E:
                p_11 = Point(db_name).field(f"temp_right_bot", float('nan')).time(now)
            try:
                p_12 = Point(db_name).field(f"humid_right_bot", float(t[4]["humidity"])).time(now)
            except IndexError as E:
                p_12 = Point(db_name).field(f"temp_left_top", float('nan')).time(now)
            
            try:
                p_13 = Point(db_name).field(f"temp_right_top",  float(t[5]["temperature"])).time(now)
            except IndexError as E:
                p_13 = Point(db_name).field(f"temp_left_top", float('nan')).time(now)
            try:
                p_14 = Point(db_name).field(f"humid_right_top", float(t[5]["humidity"])).time(now)
            except IndexError as E:
                p_14 = Point(db_name).field(f"temp_left_top", float('nan')).time(now)
            
            ## flow values
            try:
                p_15 = Point(db_name).field(f"flow_left", float(f["flow_left"])).time(now)
            except IndexError as E:
                p_15 = Point(db_name).field(f"flow_left", float("nan")).time(now)
            try:
                p_16 = Point(db_name).field(f"flow_right", float(f["flow_right"])).time(now)
            except IndexError as E:
                p_16 = Point(db_name).field(f"flow_right", float("nan")).time(now)
            
            ## pt100 values
            try:
                p_17 = Point(db_name).field(f"water_temp_ri_in",  float(p["in_ri"])).time(now)
            except IndexError as E:
                p_17 = Point(db_name).field(f"water_temp_ri_in",  float("nan")).time(now)
            try:
                p_18 = Point(db_name).field(f"water_temp_ri_out", float(p["out_ri"])).time(now)
            except IndexError as E:
                p_18 = Point(db_name).field(f"water_temp_ri_out", float("nan")).time(now)
            try:
                p_19 = Point(db_name).field(f"water_temp_le_in", float(p["in_le"])).time(now)
            except IndexError as E:
                p_19 = Point(db_name).field(f"water_temp_le_in", float("nan")).time(now)
            try:
                p_20 = Point(db_name).field(f"water_temp_le_out", float(p["out_le"])).time(now)
            except IndexError as E:
                p_20 = Point(db_name).field(f"water_temp_le_out", float("nan")).time(now)

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

        if self.number_of_scales == 2:
            head = "\n\033[33mscale_left\033[39m | \033[33mscale_right\033[39m | \033[31mt_left_top\033[39m | \033[31mt_left_bot\033[39m | \033[31mt_mid_top\033[39m  | \033[31mt_mid_bot\033[39m  | \033[31mt_right_top\033[39m | \033[31mt_right_bot\033[39m "
            head += "| \033[36mh_left_top\033[39m | \033[36mh_left_bot\033[39m | \033[36mh_mid_top\033[39m  | \033[36mh_mid_bot\033[39m | \033[36mh_right_top\033[39m | \033[36mh_right_bot\033[39m | \033[35mflow_left\033[39m | \033[35mflow_right\033[39m | "
            head += "\033[93mwtr_in_le\033[39m | \033[93mwtr_out_le\033[39m | \033[93mwtr_in_ri\033[39m | \033[93mwtr_out_ri\033[39m | \n"
            head += "-" * 276
            
            if counter % 10 == 0:
                print(head)
            out = ""
            out += f"""\033[33m{my_format(w["00"])}\033[39m |  \033[33m{my_format(w["01"])}\033[36m | """

            out += f"""\033[31m{my_format(t[1]["temperature"])}\033[39m | \033[31m{my_format(t[0]["temperature"])}\033[39m | \033[31m{my_format(t[3]["temperature"])}\033[39m | \033[31m{my_format(t[2]["temperature"])}\033[39m |  \033[31m{my_format(t[5]["temperature"])}\033[39m |  \033[31m{my_format(t[4]["temperature"])}\033[39m | """
            out += f"""\033[36m{my_format(t[1]["humidity"])}\033[39m | \033[36m{my_format(t[0]["humidity"])}\033[39m | \033[36m{my_format(t[3]["humidity"])}\033[39m | \033[36m{my_format(t[2]["humidity"])}\033[39m | \033[36m{my_format(t[5]["humidity"])}\033[39m | \033[36m{my_format(t[4]["humidity"])}\033[39m | """

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
                
            if hasattr(self, "flow"):
                f = self.flow.get_flow()
            else:
                f = None
                
            if hasattr(self, "pt100s"): 
                p = self.pt100s.get_temps()   
            else:
                p = None
                

            self.print_to_terminal(counter=counter, w=w, t=t, f=f, p=p)
            counter += 1
            time.sleep(self.wait_time)
