from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QTimer

# Import the custom UI widgets
from ui.sidebar import StationSidebar
from ui.charts_panel import ChartsPanel
from ui.alert_panel import AlertPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
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

        # Initialize UI Components (assuming they are defined in your scope)
        self.sidebar = StationSidebar(self)
        self.charts  = ChartsPanel(self)
        self.alerts  = AlertPanel(self)
        
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
        
        # Adjusted for modern widescreen ratios (e.g. 300px sidebar, remainder is charts)
        splitter.setSizes([300, 980])
        splitter.setChildrenCollapsible(False) # Prevent users from accidentally hiding a panel!
        
        self.setCentralWidget(splitter)
        
        # 2-second UI refresh polling
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)
        
    def refresh(self):
        """
        Master refresh loop to fetch the newest SQLite telemetry
        and push it to the Charts and Alert panels.
        """
        pass