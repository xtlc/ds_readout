import bme680
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque
from datetime import datetime, timedelta
from scipy.interpolate import make_interp_spline

try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)

MAX_DATA_POINTS = 500
TIME_WINDOW_SECONDS = 10

times = deque(maxlen=MAX_DATA_POINTS)
pressures = deque(maxlen=MAX_DATA_POINTS)

# --- 3. Matplotlib Setup ---
fig, ax = plt.subplots(figsize=(10, 6))
line, = ax.plot([], [], label="Druck (mBar)", color="blue") 
min_line, = ax.plot([], [], label="Min (10s)", color="red", linestyle="--")
max_line, = ax.plot([], [], label="Max (10s)", color="green", linestyle="--")

ax.set_xlabel("Zeit (letzte 10 Sekunden)")
ax.set_ylabel("Druck (mBar)") 
ax.set_title("Live-Messung des Luftdrucks")
ax.grid(True)
ax.legend()
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
text_stats = None

# --- Aktualisierungsfunktion ---
def update_plot(i):
    global text_stats

    if sensor.get_sensor_data():
        now = datetime.now()
        times.append(now)
        pressures.append(sensor.data.pressure) 
        time_limit = now - timedelta(seconds=TIME_WINDOW_SECONDS)
        
        filtered_times = [t for t in times if t > time_limit]
        filtered_pressures = [p for t, p in zip(times, pressures) if t > time_limit]

        # --- Glättung der Kurve ---
        if filtered_times and len(filtered_times) > 3:
            time_num = plt.matplotlib.dates.date2num(filtered_times)
            
            # Cubic Spline-Interpolator
            time_smooth = np.linspace(time_num.min(), time_num.max(), 300)
            spline = make_interp_spline(time_num, filtered_pressures, k=3)
            pressure_smooth = spline(time_smooth)
            
            # Konvertiere die geglätteten numerischen Zeiten zurück zu Datetime-Objekten 
            times_smooth_dt = plt.matplotlib.dates.num2date(time_smooth)
            
            # Plot-Daten setzen mit geglätteten Daten
            line.set_data(times_smooth_dt, pressure_smooth)

        else:
            # Fallback, wenn nicht genügend Daten für Spline-Interpolation vorhanden sind
            line.set_data(filtered_times, filtered_pressures)

        # Achsen anpassen für den "Live-Effekt"
        if filtered_times:
            # Setze das x-Limit auf das 10-Sekunden-Fenster
            ax.set_xlim(filtered_times[0], filtered_times[-1] + timedelta(milliseconds=100))
            
            # Berechne Min/Max für Skala und Statistik
            if filtered_pressures:
                mittel = sum(filtered_pressures) / len(filtered_pressures)
                minimum = min(filtered_pressures)
                maximum = max(filtered_pressures)
                aktuell = filtered_pressures[-1]
            else:
                 mittel, minimum, maximum, aktuell = 0, 0, 0, 0

            # Der Abstand wird bei mBar viel kleiner gewählt (z.B. 0.1 mBar)
            y_min_scale = minimum - 0.1 
            y_max_scale = maximum + 0.1
            
            # y-Limit dynamisch setzen
            ax.set_ylim(y_min_scale, y_max_scale)
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%H:%M:%S"))

            # --- Aktualisierung der Min/Max-Linien ---
            x_min, x_max = ax.get_xlim()
            
            min_line.set_xdata([x_min, x_max])
            min_line.set_ydata([minimum, minimum])
            
            max_line.set_xdata([x_min, x_max])
            max_line.set_ydata([maximum, maximum])
            
            # --- Statistik-Text ---
            stats_text = (
                f"Aktuell: {aktuell:.0f} mBar\n" 
                f"Mittel (10s): {mittel:.0f} mBar\n" 
                f"Min (10s): {minimum:.0f} mBar\n" 
                f"Max (10s): {maximum:.0f} mBar"
            )

            if text_stats is None:
                text_stats = ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, verticalalignment="top", bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.8))
            else:
                text_stats.set_text(stats_text) 
            
    return line, min_line, max_line, text_stats

# Starten der Animation ---
ani = animation.FuncAnimation(fig, update_plot, interval=50, blit=True, cache_frame_data=False)

try:
    plt.show()
except KeyboardInterrupt:
    print("Plotting beendet.")
    pass