# -*- coding: utf-8 -*-
#!/usr/bin/python3
##################################
# MLX90640 Thermal Camera w Raspberry Pi
##################################
import time, board, busio
import numpy as np
import adafruit_mlx90640
from datetime import datetime
import cv2
import cmapy
from scipy import ndimage
from pathlib import Path

class IRCam:
    def __init__(self, image_width:int=1200, image_height:int=900, foldername="rclone", name_left=None, name_right=None):#, output_folder:str = '/home/pi/pithermalcam/saved_snapshots/'):
        self.image_width=image_width
        self.image_height=image_height
        self.output_folder=Path.cwd().joinpath(foldername)
        self._setup_therm_cam()
        self._t0 = time.time()
        self.Tmin = 5
        self.Tmax = 30
        self.name_left = name_left
        self.name_right = name_right

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

        # add captures
        img_with_catpures = self._add_captures(img=combined_image)
        
        fname = self.output_folder.joinpath(f"""IR_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg""")
        cv2.imwrite(fname, img_with_catpures)
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
        cv2.putText(color_scale, f"{self.Tmin}", (0, 30),    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"10",          (280, 30),  cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"20",          (580, 30),  cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"30",          (880, 30),  cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(color_scale, f"{self.Tmax}", (1170, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

        return color_scale

    def _add_captures(self, img):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get the dimensions of the image
        height, width, _ = img.shape

        # Get the size of the text to be added
        now_size = cv2.getTextSize(now, cv2.FONT_HERSHEY_DUPLEX, 1, 2)[0]
        
        # Calculate the position for the text to be centered
        now_x = (width - now_size[0]) // 2

        # Add the text to the image
        cv2.putText(img, now, (now_x, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # adding names
        if self.name_left and self.name_right:
            cv2.putText(img, self.name_left, (10, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(img, self.name_right, (width - 10 - cv2.getTextSize(self.name_right, cv2.FONT_HERSHEY_DUPLEX, 1, 2)[0][0], 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        return img

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
        self._image = np.clip(self._image, 0, 255) # clip values to be in range [0 ... 255]
        self._image = self._image.astype(np.uint8) #convert to uint8
        self._image = cv2.applyColorMap(self._image, cv2.COLORMAP_JET)
        self._image = cv2.flip(self._image, 1)

irc = IRCam()
irc.save_image()