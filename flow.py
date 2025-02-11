import time
import RPi.GPIO as GPIO

class Flow:
    def __init__(self, FLOW_SENSOR_GPIO_RIGHT=13, FLOW_SENSOR_GPIO_LEFT=12):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FLOW_SENSOR_GPIO_RIGHT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(FLOW_SENSOR_GPIO_LEFT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.gpio_right = FLOW_SENSOR_GPIO_RIGHT
        self.gpio_left = FLOW_SENSOR_GPIO_LEFT
        self.count_right = 0
        self.count_left = 0
        self.start_counter_right = 0
        self.start_counter_left = 0

        # Initialize sensor states
        # self.counters = {"right": {"start": 0, "count": 0 }, "left": {"start": 0, "count": 0 }}

        # Add event detection for both GPIO pins
        GPIO.add_event_detect(self.gpio_right, GPIO.FALLING, callback=self.countPulse1)
        GPIO.add_event_detect(self.gpio_left, GPIO.FALLING, callback=self.countPulse2)
        print("flow sensors initiated ...")

    def countPulse1(self, channel):
        if self.start_counter_right == 1:
            self.count_right += 1

    def countPulse2(self, channel):
        if self.start_counter_left == 1:
            self.count_left += 1

    def get_flow(self):
        self.start_counter_right = 1
        self.start_counter_left = 1

        time.sleep(1)
        self.start_counter_right = 0
        self.start_counter_left = 0

        flow_right = (self.count_right / 23)  # Adjust the divisor as needed
        flow_left = (self.count_left / 23)  # Adjust the divisor as needed
        
        # print("Flow Sensor 1: %.3f Liter/min" % flow_right)
        # print("Flow Sensor 2: %.3f Liter/min" % flow_left)
        
        # Reset counts for the next interval
        self.count_right = 0
        self.count_left = 0

        return {"flow_right": round(flow_right, 2), "flow_left": round(flow_left, 2)}
            
            

if __name__ == "__main__":
    print("Test mode running ...")    # You can call your function here if needed
    f = Flow(FLOW_SENSOR_GPIO_RIGHT=18, FLOW_SENSOR_GPIO_LEFT=27)
    while True:
        t = f.get_flow()
        print(t)