import subprocess, threading
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path

class Cam:
    def __init__(self, left_panel="L", right_panel="R", resolution=[1920, 1080], filetype="jpeg", foldername="rclone"):
        self.res_x = resolution[0]
        self.res_y = resolution[1]
        self.foldername = foldername
        self.left_panel = left_panel
        self.right_panel = right_panel
        self.filetype = filetype
        self.qual = 100 if filetype == "jpeg" else 10

    def _shoot(self, filename):
        cmd = ["fswebcam", "-r", f"""{self.res_x}x{self.res_y}""", f"""--{self.filetype}""", f"""{self.qual}""", "--no-banner", f"{filename}.{self.filetype}"]
        subprocess.run(cmd, check=True)
        
        # Open the captured image
        image = Image.open(f"{filename}.{self.filetype}")
        draw = ImageDraw.Draw(image)

        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # load font & define position
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Example for Linux
        font_size = 68 
        font = ImageFont.truetype(font_path, font_size)
        bbox_timestamp = draw.textbbox((0, 0), timestamp, font=font)  # Get the bounding box of the text
        timestamp_size = bbox_timestamp[2] - bbox_timestamp[0]  # Width of the text

        bbox_right = draw.textbbox((0, 0), self.right_panel, font=font)  # Get the bounding box of the text
        right_panel_size = bbox_right[2] - bbox_right[0]
        
        pos_l = (10, 20)
        pos_m = ((self.res_x - timestamp_size) // 2, 20)  # Centered at the top
        pos_r = ((self.res_x - right_panel_size) -10 , 20)  # Centered at the top

        # Add the timestamp to the image
        draw.text(pos_l, self.left_panel, fill="red", font=font)
        draw.text(pos_m, timestamp, fill="red", font=font)
        draw.text(pos_r, self.right_panel, fill="red", font=font)

        # Save the modified image
        image.save(f"{self.foldername}/{filename}.{self.filetype}")
        Path(f"{filename}.{self.filetype}").unlink()
        
        return True

    def shoot(self, filename):
        thread = threading.Thread(target=self._shoot, args=(filename,))
        thread.start()
        thread.join()

if __name__ == "__main__":
    c = Cam(left_panel="test left", right_panel="test right", )
    c.shoot(filename="TEST")