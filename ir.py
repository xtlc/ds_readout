# -*- coding: utf-8 -*-
#!/usr/bin/python3
##################################
# MLX90640 Thermal Camera w Raspberry Pi
##################################
import time, board, busio
import numpy as np
import adafruit_mlx90640
import datetime as dt
import cv2
import cmapy
from scipy import ndimage
from pathlib import Path

# python -m pip install adafruit-circuitpython-mlx90640
# python -m pip install numpy
# python -m pip install scipy
# python -m pip install cmapy
# python -m pip install opencv-python



class IRCam:
    # _colormap_list=['jet','bwr','seismic','coolwarm','PiYG_r','tab10','tab20','gnuplot2','brg']
    # _interpolation_list_name = ['Nearest','Inter Linear','Inter Area','Inter Cubic','Inter Lanczos4','Pure Scipy', 'Scipy/CV2 Mixed']

    def __init__(self, image_width:int=1200, image_height:int=900):#, output_folder:str = '/home/pi/pithermalcam/saved_snapshots/'):
        self.image_width=image_width
        self.image_height=image_height
        self.output_folder=Path.cwd()
        self._setup_therm_cam()
        self._t0 = time.time()
        self.Tmin = 5
        self.Tmax = 30

    def _setup_therm_cam(self):
        """Initialize the thermal camera"""
        # Setup camera
        self.i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)  # setup I2C
        self.mlx = adafruit_mlx90640.MLX90640(self.i2c)  # begin MLX90640 with I2C comm
        self.mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ  # set refresh rate
        time.sleep(0.1)

    def _temps_to_rescaled_uints(self, f):
        """Function to convert temperatures to pixels on image"""
        f=np.nan_to_num(f)
        norm = np.uint8((f - self.Tmin) * 255 / (self.Tmax - self.Tmin))
        norm.shape = (24, 32)
        return norm

    def _pull_raw_image(self):
        """Get one pull of the raw image data"""
        # Get image
        self._raw_image = np.zeros((24*32,))
        try:
            self.mlx.getFrame(self._raw_image)  # read mlx90640
            self._raw_image=self._temps_to_rescaled_uints(self._raw_image)
        except ValueError:
            print("Math error; continuing...")
            self._raw_image = np.zeros((24*32,))  # If something went wrong, make sure the raw image has numbers
        except OSError:
            print("IO Error; continuing...")
            self._raw_image = np.zeros((24*32,))  # If something went wrong, make sure the raw image has numbers
    
    def save_image(self):
        """Save the current frame as a snapshot to the output folder."""
        self._pull_raw_image()
        self._process_raw_image()
        
        # Create the color scale
        color_scale = self._create_color_scale()
        
        # Combine the thermal image and the color scale
        combined_image = self._combine_images(self._image, color_scale)
        
        fname = self.output_folder.joinpath(f"""IR_{dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg""")
        cv2.imwrite(fname, combined_image)
        print("Thermal Image ", fname, "saved")

    def _create_color_scale(self):
        """Create a horizontal color scale image with labels."""
        # Create a gradient from Tmin to Tmax
        gradient = np.linspace(self.Tmin, self.Tmax, 256).astype(np.float32)
        
        # Normalize the gradient to uint8
        norm_gradient = np.uint8((gradient - self.Tmin) * 255 / (self.Tmax - self.Tmin))
        
        # Reshape to a 1D image (1 row, 256 columns)
        norm_gradient = norm_gradient.reshape((1, 256))

        # Apply the color map
        color_scale = cv2.applyColorMap(norm_gradient, cv2.COLORMAP_JET)  # Use OpenCV's built-in colormap
        
        # Resize the color scale to a desired width and height (horizontal)
        color_scale = cv2.resize(color_scale, (1200, 50))  # Width: 800px, Height: 50px

        # Draw the text on the color scale
        cv2.putText(color_scale, f"{self.Tmin}",    (0, 30),    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"10",             (280, 30),    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"20",             (580, 30),    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"30",             (880, 30),    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"{self.Tmax}",    (1170, 30),    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

        return color_scale

    def _combine_images(self, thermal_image, color_scale):
        """Combine the thermal image with the horizontal color scale."""
        # Resize the thermal image to maintain aspect ratio
        thermal_image_resized = cv2.resize(thermal_image, (self.image_width, self.image_height))
        
        # Create a new image with space for the color scale
        combined_image = np.zeros((thermal_image_resized.shape[0] + color_scale.shape[0], thermal_image_resized.shape[1], 3), dtype=np.uint8)
        
        # Place the thermal image in the combined image
        combined_image[:thermal_image_resized.shape[0], :thermal_image_resized.shape[1]] = thermal_image_resized
        
        # Place the color scale in the combined image below the thermal image
        combined_image[thermal_image_resized.shape[0]:, :color_scale.shape[1]] = color_scale
        return combined_image
    
    def _process_raw_image(self):
        self._image = ndimage.zoom(self._raw_image, 25)  # interpolate with scipy
        self._image = cv2.applyColorMap(self._image, cmapy.cmap("jet"))
        self._image = cv2.flip(self._image, 1)

irc = IRCam()
irc.save_image()