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

DS18B20s = {"in_ri": "0000006a2c70", "out_ri": "0000006ada1a", "in_le": "d5d3f91d64ff", "out_le": "a7d0f91d64ff"}
MUX = env("MUX")

# ENS210s = {"top_left": 103, "bot_left": 100, "top_mid": 106, "bot_mid": 105, "top_right": 109, "top_left": 107}
ENS210s = {"top_left": "n", "bot_left": "o", "top_mid": "p", "bot_mid": "q", "top_right": "m", "bot_right": "k"}

## helper for the ENS210:
#   100 -> d    101 -> e    102 -> f    103 -> g    104 -> h    105 -> i    106 -> j    107 -> k    108 -> l    
#   109 -> m    110 -> n    111 -> o    112 -> p    113 -> q    114 -> r    115 -> s

def zero_all_scales():
    print("Executing zero_all_scales()...")
    from scales import Mux
    s = Mux()
    s.zero_all_scales()

def to_terminal():
    from measure import Measurement
    m = Measurement(name_left=scale_left,
                    name_right=scale_right,
                    pt100s=DS18B20s,
                    ens210s=ENS210s,
                    measurements=0, 
                    sleep_time=3, 
                    foldername=foldername,
                    ircam=False,
                    cam=False)
    m.to_terminal()
    print("Executing to_terminal()...")

def to_influx():
    from measure import Measurement
    m = Measurement(name_left=scale_left,
                    name_right=scale_right,
                    pt100s=DS18B20s,
                    ens210s=ENS210s,
                    measurements=0, 
                    sleep_time=60, 
                    foldername=foldername,
                    ircam=True, 
                    cam=True)
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
