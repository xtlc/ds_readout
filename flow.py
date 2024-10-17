import time
import RPi.GPIO as GPIO


class Flow:
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


print(Flow().get_flow())