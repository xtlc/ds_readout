#!/usr/bin/python3
import numpy as np
from pathlib import Path
import os, time, logging, serial
from mi48 import MI48, format_header, format_framestats
from utils import data_to_frame, connect_senxor
from matplotlib import pyplot as plt
from PIL import Image
from influxdb_client import InfluxDBClient, Point 
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


class IRCam2:
    BARWIDTH = 4
    PIXELS = [80, 62]
    def __init__(self, name_left, name_right, sleep_time, filename, db_name=None, bucket=None):
        self.filename = filename
        self.db_name = db_name
        self.name_left = name_left
        self.name_right = name_right
        self.sleep_time = sleep_time
        self.bucket = bucket
        self.mi48, connected_port, port_names = connect_senxor()

        # initiate single frame acquisition
        self.mi48.start(stream=False, with_header=True)
        self.file = open(self.filename, mode="w", newline="")
        self.csvwriter = csv.writer(self.file)
        self.csvwriter.writerow(f"""timestamp/t{self.name_left}\t{self.name_right}""")

        # InfluxDB parameters
        if self.bucket:
            self.token = env("INFLUX_TOKEN")
            self.org = "abaton_influx"
            self.host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
            self.host = "127.0.0.1:8186"
            self.bucket = self.bucket
            self.client = InfluxDBClient(url=self.host, token=self.token, org=self.org)

        while True:
            self.timestamp = f"""{time.strftime("%Y%m%d_%H%M%S")}"""
            self.shoot(timestamp=timestamp)
            time.sleep(self.sleep_time)

    def shoot(self, timestamp=f"""{time.strftime("%Y%m%d_%H%M%S")}"""):
        self.mi48.start(stream=False, with_header=True)
        data, header = self.mi48.read()
        img = data_to_frame(data, self.mi48.fpa_shape)
        self.area = self.get_area()
        a, b = self.get_temperatures(img_array=img)
        fn = self.get_image(img_array=img, timestamp=timestamp)
        print(a, "---", b)
        print(self.area)
        if self.bucket != None:
            self.to_influx(v1=a, v2=b)
        self.write_to_csv(timestamp=timestamp, v1=a, v2=b)
        return None

    def to_influx(self, v1, v2):
        now = datetime.utcnow().replace(microsecond=0)
        write_to_influx = self.client.write_api(write_options=SYNCHRONOUS)
        p1 = Point(self.db_name).field(self.name_left, float(v1) * 1000, ).time(now)
        p2 = Point(self.db_name).field(self.name_right, float(v2) * 1000, ).time(now)
        write_to_influx.write(bucket=self.bucket, record=[p1, p2])
        return None

    def get_area(self):
        return 0, self.PIXELS[0]//2-self.BARWIDTH//2, self.PIXELS[0]//2+self.BARWIDTH//2, self.PIXELS[0]

    def get_temperatures(self, img_array):
        left_area = img_array[:, :self.area[1]]
        right_area = img_array[:, self.area[2]:]
        return np.mean(left_area), np.mean(right_area)

    def get_image(self, img_array, timestamp):
        img_L = img_array[:, :self.area[1]]
        img_R = img_array[:, self.area[2]:]
        plt.imsave(f"""{timestamp}_left.png""", img_L.astype(np.float32), cmap="coolwarm")
        plt.imsave(f"""{timestamp}_right.png""", img_R.astype(np.float32), cmap="coolwarm")
        return True

    def write_to_csv(self, timestamp, v1,v 2): 
        self.writecsvwriterr.writerow([timestamp, v1, v2])


if __name__ == "__main__":
    irc = IRCam2()
    irc.shoot()
    print("all done")
