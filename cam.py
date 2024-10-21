import subprocess
import threading


class Cam:
    def __init__(self, resolution=[1920, 1080], filetype="jpeg"):
        self.res_x = resolution[0]
        self.res_y = resolution[1]
        self.filetype = filetype
        self.qual = 100 if filetype == "jpeg" else 10

    def _shoot(self, filename):
        cmd = ["fswebcam", "-r", f"""{self.res_x}x{self.res_y}""", f"""--{self.filetype}""", f"""{self.qual}""", filename]
        subprocess.run(cmd, check=True)
        return True

    def shoot(self, filename):
        thread = threading.Thread(target=self._shoot, args=(filename,))
        thread.start()
        thread.join()