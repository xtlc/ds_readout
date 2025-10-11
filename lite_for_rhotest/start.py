from environs import Env
import argparse
from ir import IRCam2

# Initialize the environment & read env file
env = Env()
env.read_env()

def to_terminal():
    IRCam2(name_left="rho=1.5", name_right="rho=1.3", sleep_time=60, filename="test").loop()
    print("Executing to_terminal()...")

def to_influx():
    IRCam2(name_left="rho=1.5", name_right="rho=1.3", sleep_time=60, db_name="rhotest", bucket=env("BUCKET"), token=env("INFLUX_TOKEN")).loop()
    print("Executing to_influx()...")

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="Choose an option to execute a function.")

    # Add a command-line argument for the option
    parser.add_argument("option", type=int, choices=[1, 2], help="Choose an option: 1 for to_terminal, 2 for to_influx")

    # Parse the arguments
    args = parser.parse_args()

    # Execute the corresponding function based on the option
    if args.option == 1:
        to_terminal()
    elif args.option == 2:
        to_influx()
    else:
        print("no valid option was chosen.\n - 0 = zero scales\n - 1 = test output to terminal\n - 2 write to influx\n - rclone")

if __name__ == "__main__":
    main()
