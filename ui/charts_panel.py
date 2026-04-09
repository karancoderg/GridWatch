import matplotlib
matplotlib.use('qtagg')  # Ensure we render straight into PyQt6

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
from typing import Optional

from models.enums import SensorType
from models.reading import TelemetryReading
from data.store import GridWatchStore

class ChartsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Deep dark theme structure for the matplotlib canvas
        self.figure = Figure(facecolor='#1E293B', edgecolor='#1E293B')
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        # Create the 3 distinct subplots mapping each dimension exclusively
        self.ax_voltage = self.figure.add_subplot(311, facecolor='#0F111A')
        self.ax_temp = self.figure.add_subplot(312, facecolor='#0F111A')
        self.ax_load = self.figure.add_subplot(313, facecolor='#0F111A')
        
        # Pull margins to maximize plot viewing spacing dynamically 
        self.figure.subplots_adjust(hspace=0.6, top=0.92, bottom=0.08, left=0.08, right=0.95)
        
        self.current_station_id: Optional[str] = None

    def _setup_axis(self, ax):
        """Skins the native Matplotlib axes strictly unifying it tightly into the UI."""
        ax.tick_params(colors='#94A3B8', labelsize=8)
        for spine in ax.spines.values():
            spine.set_color('#334155')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    def refresh_charts(self, station_id: str, store: GridWatchStore):
        """Forces physical plots to update rapidly via polling loop."""
        self.current_station_id = station_id
        
        # Pluck 3 arrays of real telemetry mapped perfectly per unit
        readings_vol = self._get_readings_for_sensor(station_id, SensorType.VOLTAGE, store)
        readings_tmp = self._get_readings_for_sensor(station_id, SensorType.TEMPERATURE, store)
        readings_lod = self._get_readings_for_sensor(station_id, SensorType.LOAD, store)
        
        self._plot_sensor(self.ax_voltage, readings_vol, SensorType.VOLTAGE, unit="V")
        self._plot_sensor(self.ax_temp, readings_tmp, SensorType.TEMPERATURE, unit="°C")
        self._plot_sensor(self.ax_load, readings_lod, SensorType.LOAD, unit="%")
        
        self.canvas.draw()

    def _get_readings_for_sensor(self, station_id: str, sensor_type: SensorType, store: GridWatchStore) -> list[TelemetryReading]:
        query = """
            SELECT r.id, r.sensor_id, r.value, r.timestamp, r.is_anomaly
            FROM readings r
            JOIN sensors s ON r.sensor_id = s.id
            WHERE s.station_id = ? AND s.type = ?
            ORDER BY r.timestamp DESC
            LIMIT 100
        """
        readings = []
        with store.get_connection() as conn:
            rows = conn.execute(query, (station_id, sensor_type.value)).fetchall()
            
        # Reverse list natively inside python for Chart direction (left->right time flow)
        for row in reversed(rows):
            dt = datetime.fromisoformat(row['timestamp'])
                
            r = TelemetryReading(
                id=row['id'],
                sensor_id=row['sensor_id'],
                value=row['value'],
                timestamp=dt
            )
            r.is_anomaly = bool(row['is_anomaly'])
            readings.append(r)
            
        return readings

    def _plot_sensor(self, ax, readings: list[TelemetryReading], sensor_type: SensorType, unit: str):
        ax.clear()
        self._setup_axis(ax)
        
        if not readings:
            ax.set_title(f"{sensor_type.value.capitalize()} (Buffering Data...)", color='#E2E8F0', fontsize=12)
            return
            
        # Extract native float / physical data logic array streams!
        values = [r.value for r in readings]
        times  = [r.timestamp for r in readings]
        
        ax.plot(times, values, linewidth=1.5, color='#3B82F6') # Primary action plot line
        
        # Filter purely for mathematical limit breaches and draw them explicitly over the lines!
        anomalies = [r for r in readings if r.is_anomaly]
        if anomalies:
            ax.scatter(
                [r.timestamp for r in anomalies],
                [r.value for r in anomalies],
                color='#EF4444', zorder=5, s=30 # Dynamic red scatter points on top!
            )
            
        # Update specific title details cleanly
        latest_val = values[-1]
        ax.set_title(f"{sensor_type.value.capitalize()} • Active: {latest_val} {unit}", color='#E2E8F0', fontsize=11)
        ax.set_ylabel(unit, color='#94A3B8')
