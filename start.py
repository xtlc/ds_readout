from environs import Env
import argparse, subprocess, threading

##### ENTER THE NAMES OF THE PANELS ######
scale_left = "PREBATCH"
scale_right = "CS9"

##### for the remote saving of files ##### THIS FOLDER MUST EXIST BEFORE START #####
foldername = "rclone"
####################################################################################


# Initialize the environment & read env file
env = Env()
env.read_env()

# teststand #2
# DS18B20s = {"in_ri": "187a7c1f64ff", "out_ri": "ca8a7d1f64ff", "in_le": "f6f8510a6461", "out_le": "1df9510a6461"}

#teststand #1
# DS18B20s = {"in_ri": "0000006a2c70", "out_ri": "0000006ada1a", "in_le": "d5d3f91d64ff", "out_le": "a7d0f91d64ff"}

## scales
MUX = env("MUX")

## DS18B20s
# DS18B20s = {"in_ri":    env("DS18B20_IN_RIGHT"), 
#             "out_ri":   env("DS18B20_OUT_RIGHT"), 
#             "in_le":    env("DS18B20_IN_LEFT"), 
#             "out_le":   env("DS18B20_OUT_LEFT")}



## helper for the ENS210:
#   100 -> d    101 -> e    102 -> f    103 -> g    104 -> h    105 -> i    106 -> j    107 -> k    108 -> l    
#   109 -> m    110 -> n    111 -> o    112 -> p    113 -> q    114 -> r    115 -> s

def zero_all_scales():
    print("Executing zero_all_scales()...")
    from scales import Mux
    s = Mux()
    s.zero_all_scales()
    s.get_all_weights()

def to_terminal():
    from measure import Measurement
    m = Measurement(name_left=scale_left,
                    name_right=scale_right,
                    measurements=0, 
                    sleep_time=3, 
                    foldername=foldername)
    m.to_terminal()
    print("Executing to_terminal()...")

def to_influx():
    from measure import Measurement
    m = Measurement(name_left=scale_left,
                    name_right=scale_right,
                    measurements=0, 
                    sleep_time=60, 
                    foldername=foldername)
    m.to_influx(db_name="teststand_1")
    print("Executing to_influx()...")

def start_rclone(foldername="rclone"):
    cmd = ["rclone", "sync", f"""/home/rabaton/Desktop/ds_readout/{foldername}/""", f"""gdrive:00_Entwicklung und Forschung/100_Klimakammer/teststand_1/""", "-vv"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("syncing done")
    return True

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Choose an option to execute a function.")

    # Add a command-line argument for the option
    parser.add_argument("option", type=int, choices=[0, 1, 2, 3], help="Choose an option: 0 for zero_all_scales, 1 for to_terminal, 2 for to_influx")

    # Parse the arguments
    args = parser.parse_args()

    # Execute the corresponding function based on the option
    if args.option == 0:
        zero_all_scales()
    elif args.option == 1:
        to_terminal()
    elif args.option == 2:
        thread_influx = threading.Thread(target=to_influx, args=())
        thread_influx.start()
        thread_influx.join()
    elif args.option == 3:
        start_rclone(foldername=foldername)
    else:
        print("no valid option was chosen.\n - 0 = zero scales\n - 1 = test output to terminal\n - 2 write to influx\n - rclone")

if __name__ == "__main__":
    main()
