from environs import Env
from measure import Measurement
import argparse

# Initialize the environment & read env file
env = Env()
env.read_env()

# InfluxDB parameters
token = env("INFLUX_TOKEN")
org = "abaton_influx"
host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
host = "127.0.0.1:8186"
bucket = env("BUCKET")

# mux_dict = {1: {"uid": "0120211005135155", "comment": "mux_4kg_1", "number_of_scales": 8}, 
#             2: {"uid": "0120211005135902", "comment": "mux_4kg_2", "number_of_scales": 8},
#             3: {"uid": "0020240425142741", "comment": "mux_8kg_1", "number_of_scales": 4},}  
# 
PT100s = {"in_ri": "0000006a2c70", "out_ri": "0000006ada1a", "in_le": "d5d3f91d64ff", "out_le": "a7d0f91d64ff"},
USB_TEMP = "ttyUSB1"
USB_SCALE = "ttyUSB0"
FLOW_GPIOs = [12, 13]
MUX = "0020240425142741"



def zero_all_scales():
    print("Executing zero_all_scales()...")
    from scales import Mux
    s = Mux(device=USB_SCALE, uid=MUX, number_of_scales=2, max_values=0, sleep_time=0)
    s.zero_all_scales()

def to_terminal():
    m = Measurement(device_temp_usb=USB_TEMP, 
                    device_scale_usb=USB_SCALE, 
                    pt100s=PT100s,
                    scale_uid=MUX, 
                    device_flow_GPIOs=FLOW_GPIOs, 
                    number_of_scales=2, 
                    measurements=0, 
                    sleep_time=3, 
                    host=host, 
                    token=token, 
                    bucket=bucket, 
                    org=org, 
                    ircam=False,
                    cam=False)
    m.to_terminal()
    print("Executing to_terminal()...")

def to_influx():
    m = Measurement(device_temp_usb=USB_TEMP, 
                    device_scale_usb=USB_SCALE, 
                    pt100s=PT100s,
                    scale_uid=MUX, 
                    device_flow_GPIOs=FLOW_GPIOs, 
                    number_of_scales=2, 
                    measurements=0, 
                    sleep_time=60, 
                    host=host, 
                    token=token, 
                    bucket=bucket, 
                    org=org,
                    ircam=True, 
                    cam=True)
    m.to_influx()
    print("Executing to_influx()...")



def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Choose an option to execute a function.")

    # Add a command-line argument for the option
    parser.add_argument("option", type=int, choices=[0, 1, 2], help="Choose an option: 0 for zero_all_scales, 1 for to_terminal, 2 for to_influx")

    # Parse the arguments
    args = parser.parse_args()

    # Execute the corresponding function based on the option
    if args.option == 0:
        zero_all_scales()
    elif args.option == 1:
        to_terminal()
    elif args.option == 2:
        to_influx()
    elif args.option == 3:
        test()

if __name__ == "__main__":
    main()
