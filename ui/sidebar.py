from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

from models.enums import Severity
from data.store import GridWatchStore
from services.station_status import compute_station_color, get_alert_count

class StationSidebar(QWidget):
    # Emit the station_id when clicked so other panels can react seamlessly
    station_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.title = QLabel("Network Stations")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        self.layout.addWidget(self.title)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 4px;
            }
            QListWidget::item:selected {
                background-color: #2D3748; /* Slight lift on click */
                border-left: 4px solid #3B82F6; /* Action accent */
            }
            QListWidget::item:hover:!selected {
                background-color: #1E293B;
            }
        """)
        self.layout.addWidget(self.list_widget)
        
        # Connect clicking functionality
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.current_station_id = None

    def _create_color_icon(self, severity: Severity) -> QIcon:
        """Physically paints an antialiased perfect circle dynamically colored to the current DB status!"""
        colors = {
            Severity.GREEN: QColor("#10B981"),  # Emerald Green (Nominal)
            Severity.YELLOW: QColor("#F59E0B"), # Amber (Warning)
            Severity.RED: QColor("#EF4444")     # Crimson (Critical)
        }
        
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        # Drop a pure circle
        painter.setBrush(colors.get(severity, QColor("#10B981")))
        painter.drawEllipse(6, 6, 12, 12)
        painter.end()
        
        return QIcon(pixmap)

    def refresh_stations(self, store: GridWatchStore):
        """Called by MainWindow timer to pull real live data from SQLite."""
        # 1. Store the selected item so the UI doesn't visually jump when re-rendered
        selected_id = None
        if self.list_widget.currentItem():
            selected_id = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        if not selected_id:
            selected_id = self.current_station_id
                
        self.list_widget.clear()
        
        # 2. Extract database structure natively
        with store.get_connection() as conn:
            stations = conn.execute("SELECT id, name FROM stations ORDER BY name").fetchall()
            
        station_data = []
        for st in stations:
            st_id = st['id']
            # The backend engines built earlier do all the heavy lifting!
            sev = compute_station_color(st_id, store)
            alerts = get_alert_count(st_id, store)
            station_data.append({
                'id': st_id,
                'name': st['name'],
                'severity': sev,
                'alerts': alerts
            })
            
        # Aggressively dynamically sort the data stream directly on every pulse!
        # Priority 1: Highest Severity
        # Priority 2: Highest Alert Count within that Severity layer
        station_data.sort(key=lambda s: (-s['severity'].value, -s['alerts']))
            
        for idx, st in enumerate(station_data):
            st_id = st['id']
            st_name = st['name']
            sev = st['severity']
            alerts = st['alerts']
            
            alert_text = f" ({alerts} ↑)" if alerts > 0 else ""
            
            # 3. Compile the visual element!
            item = QListWidgetItem(f"{st_name}{alert_text}")
            item.setIcon(self._create_color_icon(sev))
            # Securely tag this UI Element to the raw backend relational ID!
            item.setData(Qt.ItemDataRole.UserRole, st_id)
            
            self.list_widget.addItem(item)
            
            # Safely re-select the historically selected element
            if selected_id and st_id == selected_id:
                item.setSelected(True)
            elif idx == 0 and not selected_id:
                # Default autoselect the first station ever loaded out of convenience
                item.setSelected(True)
                self.current_station_id = st_id
                self.station_selected.emit(st_id) # Let the world know!

    def _on_item_clicked(self, item: QListWidgetItem):
        st_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_station_id = st_id
        # Emit universally
        self.station_selected.emit(st_id)
