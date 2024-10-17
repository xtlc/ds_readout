import time
import RPi.GPIO as GPIO

class Flow:
    def __init__(self, FLOW_SENSOR_GPIO_1=13, FLOW_SENSOR_GPIO_2=12):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FLOW_SENSOR_GPIO_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(FLOW_SENSOR_GPIO_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.gpio1 = FLOW_SENSOR_GPIO_1
        self.gpio2 = FLOW_SENSOR_GPIO_2
        self.count1 = 0
        self.count2 = 0
        self.start_counter_1 = 0
        self.start_counter_2 = 0

        # Add event detection for both GPIO pins
        GPIO.add_event_detect(self.gpio1, GPIO.FALLING, callback=self.countPulse1)
        GPIO.add_event_detect(self.gpio2, GPIO.FALLING, callback=self.countPulse2)

    def countPulse1(self, channel):
        if self.start_counter_1 == 1:
            self.count1 += 1

    def countPulse2(self, channel):
        if self.start_counter_2 == 1:
            self.count2 += 1

    def get_flow(self):
            self.start_counter_1 = 1
            self.start_counter_2 = 1
            time.sleep(1)
            self.start_counter_1 = 0
            self.start_counter_2 = 0
            
            flow1 = (self.count1 / 23)  # Adjust the divisor as needed
            flow2 = (self.count2 / 23)  # Adjust the divisor as needed
            
            print("Flow Sensor 1: %.3f Liter/min" % flow1)
            print("Flow Sensor 2: %.3f Liter/min" % flow2)
            
            # Reset counts for the next interval
            self.count1 = 0
            self.count2 = 0
            
            

# Create an instance of the Flow class and start monitoring
flow_monitor = Flow()
for i in range(1, 11):
    flow_monitor.get_flow() 
    print("round ", i, "done")
    time.sleep(2)       

class Flow_:
    def __init__(self, FLOW_SENSOR_GPIO=13):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FLOW_SENSOR_GPIO, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        self.gpio = FLOW_SENSOR_GPIO
        self.count = 0

    def countPulse(self, channel):
        if self.start_counter == 1:
            self.count = self.count+1

    def get_flow(self):
        GPIO.add_event_detect(self.gpio, GPIO.FALLING, callback=self.countPulse)
        while True:
            self.start_counter = 1
            time.sleep(1)
            self.start_counter = 0
            flow = (self.count/23)
            print("The flow is: %.3f Liter/min" % (flow))
            self.count = 0
            time.sleep(5)


#print(Flow().get_flow())