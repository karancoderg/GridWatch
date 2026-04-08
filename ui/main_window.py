from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QTimer

from ui.sidebar import StationSidebar
from ui.charts_panel import ChartsPanel
from ui.alert_panel import AlertPanel
from data.store import GridWatchStore

class MainWindow(QMainWindow):
    def __init__(self, store: GridWatchStore):
        super().__init__()
        
        self.store = store
        
        # Enhance window structure and naming
        self.setWindowTitle("GridWatch • Mission Control")
        self.setMinimumSize(1280, 800) # Increased size for a comfortable layout
        
        # ─── PREMIUM DARK THEME (QSS) ─────────────────────────────────────────
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F111A; /* Deep, sleek navy-dark background */
            }
            QWidget {
                color: #E2E8F0; /* Soft slate text for readability */
                font-family: 'Inter', '-apple-system', 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            /* A clean, unobtrusive splitter handle */
            QSplitter::handle {
                background-color: #1E293B;
                border-radius: 2px;
            }
            QSplitter::handle:horizontal {
                width: 4px;
                margin: 4px 0px;
            }
            QSplitter::handle:hover {
                background-color: #3B82F6; /* Bright blue accent glow when hovered */
            }
            /* The panels inside get a modern "floating card" styling */
            QWidget#RightPanel {
                background-color: #1E293B;
                border-radius: 12px;
                border: 1px solid #334155;
            }
        """)
        # ──────────────────────────────────────────────────────────────────────

        # Initialize UI Components
        self.sidebar = StationSidebar(self)
        self.charts  = ChartsPanel(self)
        self.alerts  = AlertPanel(self)
        
        # Connect clicking functionality securely
        self.sidebar.station_selected.connect(self._on_station_selected)
        
        # Structure the Right Area as a unified "Card" giving elements breathing room
        right_panel = QWidget()
        right_panel.setObjectName("RightPanel")
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20) # Smooth internal padding
        right_layout.setSpacing(20)                     # Clean gap between charts and alerts
        
        # 70/30 vertical split prioritizing the data visualization
        right_layout.addWidget(self.charts, stretch=7)  
        right_layout.addWidget(self.alerts, stretch=3)
        
        # Structure the Master Layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 980])
        splitter.setChildrenCollapsible(False) # Prevent users from accidentally hiding a panel
        
        self.setCentralWidget(splitter)
        
        # Boot initial sync instantly
        self.sidebar.refresh_stations(self.store)
        
        # Start the Background Display Poller
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)
        
    def _on_station_selected(self, station_id: str):
        """React physically when a user clicks the sidebar list!"""
        self.charts.refresh_charts(station_id, self.store)
        self.alerts.refresh_alerts(station_id, self.store)
        
    def refresh(self):
        """
        Master refresh loop to SAFELY trigger UI Cascading renders now that
        DataGenerator handles all SQLite insertions autonomously via background thread.
        """
        # 1. Trigger UI Cascading renders
        self.sidebar.refresh_stations(self.store)
        
        # 2. Only update the deeply-focused Right panels if a station is currently targeted
        active_station = self.sidebar.current_station_id
        if active_station:
            self.charts.refresh_charts(active_station, self.store)
            self.alerts.refresh_alerts(active_station, self.store)