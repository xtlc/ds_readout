#!/usr/bin/python3
import numpy as np
from pathlib import Path
import os, time, csv
from mi48 import MI48, format_header, format_framestats
from utils import data_to_frame, connect_senxor
from matplotlib import pyplot as plt
from PIL import Image
from influxdb_client import InfluxDBClient, Point 
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


class IRCam2:
    BARWIDTH = 10
    PIXELS = [80, 62]
    CMAP = "coolwarm"
    BURST_COUNT = 3
    CYCLE_TIME = 2 
    def __init__(self, name_left, name_right, sleep_time, filename, db_name=None, bucket=None, debug=False):
        self.filename = filename
        self.debug = debug
        self.db_name = db_name
        self.bucket = bucket
        self.name_left = name_left
        self.name_right = name_right
        self.sleep_time = sleep_time
        self.mi48, connected_port, port_names = connect_senxor()
        print("... initialized.")

        # initiate single frame acquisition
        self.mi48.start(stream=False, with_header=True)
        self.file = open(self.filename, mode="w", newline="")
        self.csvwriter = csv.writer(self.file, delimiter="\t")
        self.csvwriter.writerow(["timestamp", self.name_left ,self.name_right])

        # InfluxDB parameters
        if self.bucket != None:
            print("writing to influx ...")
            self.token = env("INFLUX_TOKEN")
            self.org = "abaton_influx"
            self.host = "https://eu-central-1-1.aws.cloud2.influxdata.com"
            self.host = "127.0.0.1:8186"
            self.client = InfluxDBClient(url=self.host, token=self.token, org=self.org)

    def shoot_once(self, timestamp=None):
        self.area = self.get_area()
        
        v1_list, v2_list, img_array_list = [], [], []
        for i in range(self.BURST_COUNT):
            self.mi48.start(stream=False, with_header=True)
            data, header = self.mi48.read()
            img = data_to_frame(data, self.mi48.fpa_shape)
            v1, v2 = self.get_temperatures(img_array=img)
            v1_list.append(v1)
            v2_list.append(v2)
            img_array_list.append(img)
            time.sleep(self.CYCLE_TIME)
        
        v1_mean = np.mean(v1_list)
        v2_mean = np.mean(v2_list)
        img_mean = np.mean(img_array_list, axis=0)

        fn = self.get_image(img_array=img_mean, timestamp=timestamp)
        if self.bucket != None:
            self.to_influx(v1=v1_mean, v2=v2_mean)
        return v1_mean, v2_mean

    def loop(self):
        counter = 0
        while True:
            timestamp = f"""{time.strftime("%Y%m%d_%H%M%S")}"""
            v1, v2 = self.shoot_once(timestamp=timestamp)
            self.write_to_csv(timestamp=timestamp, v1=v1, v2=v2)
            time.sleep(self.sleep_time)
            print(f"""finished at {timestamp} with mean values: {v1:2.2f} | {v2:2.2f}""")
            if counter % 10 == 0:
                self.file.flush()
            counter += 1

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

    def save_image(self, img_array, timestamp, filename="debug.png"):
        fig, ax = plt.subplots()
        im = ax.imshow(img_array.astype(np.float32), cmap=self.CMAP)
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("Temperaturwert")
        ax.axis("off")
        fig.savefig(filename, bbox_inches="tight", dpi=300)
        plt.close(fig)
        return None

    def get_image(self, img_array, timestamp):
        if self.debug:
            print("saving a debug image with colorbar...")
            self.save_image(img_array=img_array, timestamp=timestamp)
        self.save_image(img_array=img_array[:, :self.area[1]], timestamp=timestamp, filename=f"""{timestamp}_left.png""")
        self.save_image(img_array=img_array[:, self.area[2]:], timestamp=timestamp, filename=f"""{timestamp}_right.png""")
        return True

    def write_to_csv(self, timestamp, v1, v2): 
        self.csvwriter.writerow([timestamp, v1, v2])

    def __del__(self):
        # Schließt die Datei, wenn das IRCam2-Objekt zerstört wird.
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()


if __name__ == "__main__":
    irc = IRCam2(name_left="test_le", name_right="test_ri", sleep_time=0, filename="test.csv", debug=True)
    print(irc.shoot_once())
    print("all done")
