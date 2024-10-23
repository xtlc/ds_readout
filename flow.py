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
        # self.counters["right"]["start"] = 1
        # self.counters["left"]["start"] = 1
        time.sleep(1)
        self.start_counter_right = 0
        self.start_counter_left = 0
        
        # self.counters["right"]["start"] = 0
        # self.counters["left"]["start"] = 0

        flow_right = (self.count_right / 23)  # Adjust the divisor as needed
        flow_left = (self.count_left / 23)  # Adjust the divisor as needed
        
        print("Flow Sensor 1: %.3f Liter/min" % flow_right)
        print("Flow Sensor 2: %.3f Liter/min" % flow_left)
        
        # Reset counts for the next interval
        self.count_right = 0
        self.count_left = 0

        return {"flow_right": round(flow_right, 2), "flow_left": round(flow_left, 2)}
            
            

# # Create an instance of the Flow class and start monitoring
# flow_monitor = Flow()
# for i in range(1, 11):
#     flow_monitor.get_flow() 
#     print("round ", i, "done")
#     time.sleep(2)       

# class Flow_:
#     def __init__(self, FLOW_SENSOR_GPIO=13):
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(FLOW_SENSOR_GPIO, GPIO.IN, pull_up_down = GPIO.PUD_UP)
#         self.gpio = FLOW_SENSOR_GPIO
#         self.count = 0

#     def countPulse(self, channel):
#         if self.start_counter == 1:
#             self.count = self.count+1

#     def get_flow(self):
#         GPIO.add_event_detect(self.gpio, GPIO.FALLING, callback=self.countPulse)
#         while True:
#             self.start_counter = 1
#             time.sleep(1)
#             self.start_counter = 0
#             flow = (self.count/23)
#             print("The flow is: %.3f Liter/min" % (flow))
#             self.count = 0
#             time.sleep(5)


# #print(Flow().get_flow())
