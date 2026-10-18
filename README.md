# System Resource Monitor

A real-time Windows desktop application for monitoring system performance through live-updating charts and a clean graphical interface.

Built with **Python, PySide6, and Matplotlib**, this project visualizes CPU usage, memory utilization, disk activity, and network performance in one place.

## Features

- **CPU Monitoring** — Track processor utilization with a live-updating chart.
- **Memory Monitoring** — Observe system memory usage.
- **Disk Monitoring** — Visualize disk activity and performance metrics.
- **Network Monitoring** — Track network performance metrics.
- **Live Charts** — View resource history through Matplotlib visualizations.
- **Smooth Scrolling** — Navigate the interface comfortably.
- **Desktop GUI** — Clean interface built with PySide6.
- **Standalone Windows Executable** — Run the packaged application without manually running the Python script.

## Preview

<img width="2880" height="1692" alt="Screenshot 2026-10-18 215146" src="https://github.com/user-attachments/assets/c7d1fa5a-20ba-4942-9633-df02e10fe24f" />

## Tech Stack

- **Python** — Application logic and system monitoring
- **PySide6** — Desktop graphical interface
- **Matplotlib** — Real-time charts and visualization
- **PyInstaller** — Packaging the application into a Windows executable

## Getting Started

### Option 1: Run the Windows Executable

1. Open the project's **Releases** page on GitHub.
2. Download `SystemResourceMonitor.exe` from the latest release.
3. Run the executable.

No separate Python installation should be necessary for the packaged application.

### Option 2: Run from Source

#### Prerequisites

- Python installed on Windows
- Git (optional, for cloning the repository)

#### Installation

Clone the repository:

```bash
git clone https://github.com/tanmaykukreja/System-Resource-Monitor
cd System-Resource-Monitor
```

Install the required dependencies:

```bash
python -m pip install PySide6 matplotlib psutil
```

Run the application:

```bash
python main.py
```

> **Note:** The installation command assumes the project uses `psutil` for system metrics. If your `telemetry_data.py` uses additional third-party packages, install those as well.

## Project Structure

```text
SystemResourceMonitor/
├── main.py
├── telemetry_data.py
├── resource-monitor-icon.png
├── resource-monitor-icon.ico
├── README.md
├── LICENSE
└── requirements.txt
```

The generated `build/` and `dist/` folders may also exist locally after packaging.

## Built With

This project was developed to explore Python desktop application development, real-time system monitoring, data visualization, and Windows application packaging.

## Future Improvements

- Animated resource activity indicators
- Additional system performance metrics
- Customizable chart history
- More detailed hardware and software information

> **Startup Note:** The standalone Windows executable may take some time to launch, particularly on its first run. This is because the application bundles Python and its dependencies using PyInstaller's one-file packaging mode, which extracts the required files before starting. Please allow some time for the application to initialize before launching it again.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## Author

**Tanmay Kukreja**

Developed as a hands-on project in Python GUI development and system performance visualization.
