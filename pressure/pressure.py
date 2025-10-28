import bme680, time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque
from datetime import datetime, timedelta
from scipy.interpolate import make_interp_spline

class LivePlotter:
    def __init__(self):
        # sensor initialisieren
        try:
            self.sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        except (RuntimeError, IOError):
            self.sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)
        self.MAX_DATA_POINTS = 500
        self.TIME_WINDOW_SECONDS = 10
        
        # Daten-Deques
        self.times = deque(maxlen=self.MAX_DATA_POINTS)
        self.pressures = deque(maxlen=self.MAX_DATA_POINTS)
        
        # Matplotlib Setup
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        
        # Initialisierung der Linien (Hauptlinie und Min/Max)
        self.line, = self.ax.plot([], [], label="Druck (mBar, geglättet)", color="blue") 
        self.min_line, = self.ax.plot([], [], label="Min (10s)", color="red", linestyle="--")
        self.max_line, = self.ax.plot([], [], label="Max (10s)", color="green", linestyle="--")
        self.text_stats = None
        
        # Achsen- und Titel-Setup
        self.ax.set_xlabel("Zeit (letzte 10 Sekunden)")
        self.ax.set_ylabel("Druck (mBar)") 
        self.ax.set_title("Live-Messung des Luftdrucks")
        self.ax.grid(True)
        self.ax.legend()
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

    def update_plot(self, i):
        if self.sensor.get_sensor_data():
            now = datetime.now()
            
            # Daten lesen und speichern (1 hPa = 1 mBar)
            self.times.append(now)
            self.pressures.append(self.sensor.data.pressure) 
            time_limit = now - timedelta(seconds=self.TIME_WINDOW_SECONDS)
            
            # Daten filtern
            filtered_times = [t for t in self.times if t > time_limit]
            filtered_pressures = [p for t, p in zip(self.times, self.pressures) if t > time_limit]

            # Glättung der Kurve mit Cubic Spline Interpolation
            if filtered_times and len(filtered_times) > 3:
                time_num = plt.matplotlib.dates.date2num(filtered_times)
                
                # Erzeuge einen Spline-Interpolator
                time_smooth = np.linspace(time_num.min(), time_num.max(), 300)
                spline = make_interp_spline(time_num, filtered_pressures, k=3)
                pressure_smooth = spline(time_smooth)
                
                # Konvertiere die geglätteten numerischen Zeiten zurück
                times_smooth_dt = plt.matplotlib.dates.num2date(time_smooth)
                
                # Plot mit geglätteten Daten
                self.line.set_data(times_smooth_dt, pressure_smooth)

            else:
                # Fallback ohne Glättung
                self.line.set_data(filtered_times, filtered_pressures)

            # Achsen anpassen und Statistik berechnen
            if filtered_times:
                # Setze das x-Limit
                self.ax.set_xlim(filtered_times[0], filtered_times[-1] + timedelta(milliseconds=100))
                self.ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M:%S"))

                # Berechnung der Statistik (Min/Max für Linien und Text)
                if filtered_pressures:
                    mittel = sum(filtered_pressures) / len(filtered_pressures)
                    minimum = min(filtered_pressures)
                    maximum = max(filtered_pressures)
                    aktuell = filtered_pressures[-1]
                else:
                    mittel, minimum, maximum, aktuell = 0, 0, 0, 0
                
                # Skala: Min - 0.1 mBar bis Max + 0.1 mBar
                y_min_scale = minimum - 0.1 
                y_max_scale = maximum + 0.1
                self.ax.set_ylim(y_min_scale, y_max_scale)
                
                # Aktualisierung der Min/Max-Linien 
                x_min, x_max = self.ax.get_xlim()
                self.min_line.set_xdata([x_min, x_max])
                self.min_line.set_ydata([minimum, minimum])
                self.max_line.set_xdata([x_min, x_max])
                self.max_line.set_ydata([maximum, maximum])
                
                # Statistik-Text 
                stats_text = (f"""Aktuell: {aktuell:.2f} mBar\nMittel (10s): {mittel:.2f} mBar\nMin (10s): {minimum:.2f} mBar\nMax (10s): {maximum:.2f} mBar""")

                if self.text_stats is None:
                    # Initialisierung (oben links im Plot)
                    self.text_stats = self.ax.text(0.02, 0.95, stats_text, transform=self.ax.transAxes, verticalalignment="top", bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8))
                else:
                    self.text_stats.set_text(stats_text) 
                
        return self.line, self.min_line, self.max_line, self.text_stats

    def start_plotting(self):
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=50, blit=True, cache_frame_data=False)
        try:
            plt.show()
        except KeyboardInterrupt:
            print("Plotting beendet.")
            pass


plotter = LivePlotter()
plotter.start_plotting()