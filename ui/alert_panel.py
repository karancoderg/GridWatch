from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from typing import Optional

from models.enums import Severity
from data.store import GridWatchStore
from services.alert_service import get_alerts_for_station

class AlertPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.title = QLabel("🚨 Active Anomalies")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; color: #EF4444; padding: 5px;")
        self.layout.addWidget(self.title)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Severity", "Sensor", "Value", "Threshold", "Time"])
        
        # Stretch columns securely
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # Premium dark styling aligning to main_window specs
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                gridline-color: #334155;
                border: none;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1E293B;
                color: #94A3B8;
                padding: 4px;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #1E293B;
            }
        """)
        
        # Disable editing globally
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        self.layout.addWidget(self.table)
        
        self.current_station_id: Optional[str] = None

    def refresh_alerts(self, station_id: str, store: GridWatchStore):
        """Fetches anomalies for the globally selected station natively from SQLite"""
        self.current_station_id = station_id
        
        alerts = get_alerts_for_station(station_id, store, limit=20)
        
        self.table.setRowCount(len(alerts))
        for row_idx, alert in enumerate(alerts):
            # Parse core string formats
            s_type = alert.sensor_type.value.upper()
            val_str = f"{alert.value}"
            thresh_str = alert.threshold
            ts_str = alert.timestamp.strftime("%H:%M:%S")
            
            # Map Base Cell Colors Dynamically
            bg_color = QColor()
            sev_text = ""
            
            if alert.severity == Severity.RED:
                bg_color = QColor("#EF4444") # Solid Crimson
                sev_text = "CRITICAL"
            elif alert.severity == Severity.YELLOW:
                bg_color = QColor("#F59E0B") # Solid Amber
                sev_text = "WARNING"
            else:
                bg_color = QColor("#10B981") # Solid Green
                sev_text = "NORMAL"
            
            # --- Compile Standardized Grid Objects ---
            
            # Column 0: Physical severity background color!
            item_sev = QTableWidgetItem(sev_text)
            item_sev.setBackground(bg_color)
            item_sev.setForeground(QColor("#FFFFFF")) # Force crisp white text for max visual contrast
            
            # Set default text coloring cleanly across the rest of the row
            item_sensor = QTableWidgetItem(s_type)
            item_sensor.setForeground(QColor("#E2E8F0"))
            
            item_val = QTableWidgetItem(val_str)
            fnt = QFont()
            fnt.setBold(True)
            item_val.setFont(fnt)
            item_val.setForeground(QColor("#E2E8F0"))
            
            item_thresh = QTableWidgetItem(thresh_str)
            item_thresh.setForeground(QColor("#E2E8F0"))
            
            item_time = QTableWidgetItem(ts_str)
            item_time.setForeground(QColor("#94A3B8")) # Slight grey fade for timestamps
            
            # Map into strict grid order: [Severity | Sensor | Value | Threshold | Time]
            self.table.setItem(row_idx, 0, item_sev)
            self.table.setItem(row_idx, 1, item_sensor)
            self.table.setItem(row_idx, 2, item_val)
            self.table.setItem(row_idx, 3, item_thresh)
            self.table.setItem(row_idx, 4, item_time)
