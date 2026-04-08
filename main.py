import sys
import os
from PyQt6.QtWidgets import QApplication

# Import the aesthetic UI we just built!
from ui.main_window import MainWindow
from data.store import GridWatchStore
from data.generator import DataGenerator
from services.anomaly_engine import AnomalyEngine
from models.sensor import Sensor
from models.enums import SensorType

def seed_stations(store: GridWatchStore):
    """Safely builds an isolated, fresh prototype environment"""
    
    # Securely clear the environment natively if it exists
    with store.get_connection() as conn:
        conn.execute("DELETE FROM readings")
        conn.execute("DELETE FROM sensors")
        conn.execute("DELETE FROM stations")
    
    # Procedurally layout a massive 10-station dynamic grid Network!
    for i in range(1, 11):
        st_id = f"stat_{i:02d}"
        store.save_station(st_id, f"Sector {i} Substation", f"Grid {i%3}")
        
        # Deploy standard hardware configuration directly onto the node
        store.save_sensor(Sensor(f"v_{st_id}", st_id, SensorType.VOLTAGE, "V"))
        store.save_sensor(Sensor(f"t_{st_id}", st_id, SensorType.TEMPERATURE, "C"))
        store.save_sensor(Sensor(f"l_{st_id}", st_id, SensorType.LOAD, "%"))
        
def main():
    """
    Master bootloader for the GridWatch Mission Control Desktop Dashboard
    """
    app = QApplication(sys.argv)
    
    # 1. Initialize the SQLite mapping architecture completely
    store = GridWatchStore("gridwatch.db")
    seed_stations(store)          # dynamically provision 10 fake stations + 30 active sensors!
    
    # 2. Deploy Background Mathematics processing algorithms securely
    engine = AnomalyEngine()
    generator = DataGenerator(store, engine)
    generator.start()             # background daemon Python thread pumping real-time data!
    
    # 3. Instantiate and show the Main Window exclusively as a simple Native Renderer
    window = MainWindow(store)
    window.show()
    
    # 4. Enter the continuous application loop!
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
