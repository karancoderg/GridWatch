## Video Walkthrough
[VIDEO_LINK_HERE]

---

## Problem Definition
Municipal grid engineers currently manage hundreds of sub-stations by manually exporting and scanning raw log files per device. There is no existing tooling to automatically surface anomalies, forcing engineers to spend more time managing data than understanding system health. The core requirement is to instantly identify which station needs attention at any given moment, without opening a single file.

## Setup and Deployment
1. Ensure Python 3.10 or higher is installed on your system.
2. Clone the repository to your local machine:
   ```bash
   git clone <repository_url>
   cd gridwatch
   ```
3. Create a python virtual environment:
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```cmd
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Launch the application:
   ```bash
   python main.py
   ```
7. The application will automatically seed 10 fake sub-stations on the first run, requiring no manual database setup.

## Technical Architecture
The application follows a strict three-layer architectural separation consisting of models, services, and UI components. The models define the data schema, the services encapsulate all business logic, and the UI is strictly responsible for rendering. A core invariant of this architecture is that services never import from the UI layer, preventing cyclical dependencies and ensuring the business logic remains fully testable in isolation. 

At the core of the detection pipeline is the `AnomalyEngine`, which acts as a unified interface combining both standard thresholds and statistical deviation analysis. It relies on a centralized `config.py` file containing all system limits, ensuring that adjusting safety parameters requires zero changes to the underlying logic. The anomaly rules apply distinct mathematical bounds based on sensor type: voltage utilizes an absolute Z-score to flag both dangerous drops and spikes, whereas temperature and load utilize a zero-bounded Z-score since only upward surges represent a physical threat. 

Data flows into the system via a background generator thread, ensuring that database writes and statistical computations never block the primary PyQt6 event loop. The main dashboard visualizes station health based on a sliding window of the most recent 50 readings, meaning the color indicator reflects only current health. However, the underlying alert history maintains a persistent, append-only record, guaranteeing that engineers retain a complete audit trail of all anomalies even after a station's UI indicator resets.

```text
gridwatch/
├── models/        → SubStation, Sensor, TelemetryReading, enums
├── services/      → ThresholdService, ZScoreService, AnomalyEngine, StationStatusService, AlertService
├── data/          → generator.py (fake telemetry), store.py
├── ui/            → main_window, sidebar, charts_panel, alert_panel
├── tests/         → test_threshold, test_zscore, test_station_status
├── config.py      → all thresholds centralized here
└── main.py        → entry point only
```

## Critical Reflection
The primary trade-off in the current design involves the station color indicator, which is driven by a sliding window that automatically resets after 50 normal readings. This approach guarantees that the dashboard always reflects the immediate, real-time status of the grid. However, if an engineer steps away from their terminal during a brief telemetry spike, the station will silently return to a nominal state on the UI. While the persistent alert history ensures the event is recorded in the database, the immediate visual layout provides no evidence that an incident occurred recently.

Given more time, the correct architectural evolution is to implement an explicit acknowledgement system. A station would transition to an alert state upon an anomaly and remain flagged until an engineer manually reviews and clears the warning. This fundamentally shifts the UI from a time-based reset to a human-validation model, which is highly appropriate for a safety-critical monitoring deployment. Implementing this within the scope of a rapid MVP was deprioritized due to the added state management complexity, such as tracking seen versus unseen alerts, but it represents the most critical iteration for a production release.