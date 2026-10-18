import os
import sys
import time
from collections import deque
import platform

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QFrame,
    QProgressBar,
    QScrollArea,
)
from PySide6.QtGui import QIcon, QWheelEvent
from PySide6.QtCore import Qt, QTimer

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from telemetry_data import (
    static_data,
    initialize_cpu_sampling,
    recurring_sys_data,
)

def resource_path(relative_path):
    """Get the correct path for development and packaged builds."""
    base_path = getattr(
        sys,
        "_MEIPASS",
        os.path.abspath(".")
    )
    return os.path.join(base_path, relative_path)

app = QApplication(sys.argv)
initialize_cpu_sampling()

window = QMainWindow()
window.setWindowTitle("System Resource Monitor")
window.resize(1200, 800)
window.setMinimumSize(1000, 800)
window.setWindowIcon(
    QIcon(resource_path("resource-monitor-icon.png"))
)

central_widget = QWidget()
central_widget.setObjectName("centralWidget")
central_widget.setStyleSheet("""
    QWidget#centralWidget {
        background-color: #F0FDF4;
    }
""")


class SmoothScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()

        self._scroll_position = 0.0
        self._target_position = 0.0

        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(8)
        self._animation_timer.timeout.connect(self._animate_scroll)

    def wheelEvent(self, event: QWheelEvent):
        bar = self.verticalScrollBar()

        # Convert wheel movement into a target scroll position.
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return

        self._target_position -= delta * 0.8
        self._target_position = max(
            bar.minimum(),
            min(bar.maximum(), self._target_position),
        )

        if not self._animation_timer.isActive():
            self._scroll_position = float(bar.value())
            self._animation_timer.start()

        event.accept()

    def _animate_scroll(self):
        bar = self.verticalScrollBar()

        # Smoothly approach the target rather than jumping to it.
        current = float(bar.value())
        difference = self._target_position - current

        if abs(difference) < 1.0:
            bar.setValue(round(self._target_position))
            self._scroll_position = self._target_position
            self._animation_timer.stop()
            return

        new_position = current + difference * 0.22
        bar.setValue(round(new_position))

scroll_area = SmoothScrollArea()
scroll_area.setWidgetResizable(True)
scroll_area.setFrameShape(QFrame.Shape.NoFrame)

scroll_area.setStyleSheet("""
    QScrollArea {
        background-color: #F0FDF4;
        border: none;
    }

    QScrollBar:vertical {
        background: #DCFCE7;
        width: 10px;
        margin: 4px 3px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical {
        background: #059669;
        min-height: 35px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical:hover {
        background: #047857;
    }

    QScrollBar::handle:vertical:pressed {
        background: #064E3B;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
        border: none;
    }

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: transparent;
    }

    QScrollBar:horizontal {
        height: 0px;
        background: transparent;
    }
""")

# Set up the layout BEFORE placing the widget inside the scroll area.
main_layout = QVBoxLayout(central_widget)
main_layout.setContentsMargins(24, 20, 24, 20)
main_layout.setSpacing(20)

scroll_area.setWidget(central_widget)
window.setCentralWidget(scroll_area)


class NavbarButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 35);
            }
        """)


# -------------------- NAVBAR --------------------

navbar = QWidget()
navbar.setObjectName("navbar")
navbar.setFixedHeight(64)

nav_layout = QHBoxLayout(navbar)
nav_layout.setContentsMargins(20, 0, 20, 0)
nav_layout.setSpacing(12)
main_layout.addWidget(navbar)

logo_icon = QLabel()
logo_icon.setPixmap(
    QIcon(resource_path("resource-monitor-icon.png")).pixmap(32, 32)
)
logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
nav_layout.addWidget(logo_icon)

logo = QLabel("System Resource Monitor")
logo.setStyleSheet("""
    color: white;
    font-size: 16px;
    font-weight: bold;
    background: transparent;
    border: none;
""")
nav_layout.addWidget(logo)
nav_layout.addStretch()

navbar.setStyleSheet("""
    QWidget#navbar {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 #064E3B,
            stop:0.55 #059669,
            stop:1 #34D399
        );
        border: none;
        border-radius: 12px;
    }
""")


# -------------------- HEADER --------------------

header_widget = QWidget()
header_layout = QHBoxLayout(header_widget)
header_layout.setContentsMargins(0, 8, 0, 0)
header_layout.setSpacing(12)

title_layout = QVBoxLayout()
title_layout.setSpacing(4)

heading = QLabel("System Overview")
heading.setStyleSheet("""
    color: #064E3B;
    font-size: 25px;
    font-weight: bold;
    background: transparent;
    border: none;
""")

description = QLabel("Monitor your system performance at a glance")
description.setStyleSheet("""
    color: #64748B;
    font-size: 13px;
    background: transparent;
    border: none;
""")

title_layout.addWidget(heading)
title_layout.addWidget(description)
header_layout.addLayout(title_layout)
header_layout.addStretch()

main_layout.addWidget(header_widget)


# -------------------- INITIAL TELEMETRY --------------------

system_info = static_data()
current_data = recurring_sys_data()

previous_sample_time = time.monotonic()


# -------------------- RESOURCE CARD --------------------

class ResourceCard(QFrame):
    def __init__(
        self,
        title,
        value,
        percentage=None,
        subtitle="",
        line_color="#059669",
        fixed_plot_scale=True,
    ):
        super().__init__()

        self.line_color = line_color
        self.fixed_plot_scale = fixed_plot_scale
        self.history = deque(maxlen=30)

        self.setObjectName("resourceCard")
        self.setMinimumHeight(260)

        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(18, 16, 18, 16)
        self.card_layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: #64748B;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        self.card_layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("""
            color: #064E3B;
            font-size: 28px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        self.card_layout.addWidget(self.value_label)

        self.progress = None

        if percentage is not None:
            self.progress = QProgressBar()
            self.progress.setRange(0, 100)
            self.progress.setValue(
                max(0, min(100, round(percentage)))
            )
            self.progress.setTextVisible(False)
            self.progress.setFixedHeight(8)
            self.progress.setStyleSheet("""
                QProgressBar {
                    background-color: #D1FAE5;
                    border: none;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background-color: #059669;
                    border-radius: 4px;
                }
            """)
            self.card_layout.addWidget(self.progress)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        self.card_layout.addWidget(self.subtitle_label)

        self.figure = Figure(
            figsize=(3.2, 1.0),
            dpi=100,
            facecolor="#FFFFFF",
        )
        self.figure.subplots_adjust(
            left=0.01,
            right=0.99,
            top=0.95,
            bottom=0.05,
        )

        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#FFFFFF")
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        for spine in self.ax.spines.values():
            spine.set_visible(False)

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(90)
        self.canvas.setMaximumHeight(110)
        self.card_layout.addWidget(self.canvas)

        self.setStyleSheet("""
            QFrame#resourceCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)

    def update_data(self, value, percentage=None, subtitle=None):
        self.value_label.setText(value)

        if self.progress is not None and percentage is not None:
            self.progress.setValue(
                max(0, min(100, round(percentage)))
            )

        if subtitle is not None:
            self.subtitle_label.setText(subtitle)

    def update_plot(self, value):
        self.history.append(max(0.0, float(value)))

        x_values = list(range(len(self.history)))
        y_values = list(self.history)

        self.ax.clear()
        self.ax.set_facecolor("#FFFFFF")

        # Percentage charts use a fixed 0-100 scale.
        # Rate charts scale dynamically to the observed values.
        if self.fixed_plot_scale:
            self.ax.set_ylim(0, 100)
            self.ax.set_xlim(0, 29)

            for level in (25, 50, 75):
                self.ax.axhline(
                    level,
                    color="#E2E8F0",
                    linewidth=0.7,
                    linestyle="--",
                    zorder=0,
                )
        else:
            highest_value = max(y_values, default=0)
            upper_limit = max(1.0, highest_value * 1.25)
            self.ax.set_ylim(0, upper_limit)
            self.ax.set_xlim(0, 29)

            for level in (
                upper_limit * 0.25,
                upper_limit * 0.50,
                upper_limit * 0.75,
            ):
                self.ax.axhline(
                    level,
                    color="#E2E8F0",
                    linewidth=0.7,
                    linestyle="--",
                    zorder=0,
                )

        self.ax.fill_between(
            x_values,
            y_values,
            0,
            color=self.line_color,
            alpha=0.12,
            zorder=1,
        )

        self.ax.plot(
            x_values,
            y_values,
            color=self.line_color,
            linewidth=2.4,
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=3,
        )

        self.ax.scatter(
            x_values[-1],
            y_values[-1],
            s=28,
            color=self.line_color,
            edgecolors="#FFFFFF",
            linewidths=1.3,
            zorder=4,
        )

        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.margins(x=0, y=0.05)

        for spine in self.ax.spines.values():
            spine.set_visible(False)

        self.canvas.draw_idle()


# -------------------- RESOURCE CARDS --------------------

cpu_card = ResourceCard(
    "CPU Usage",
    f"{current_data['cpu_percentage']:.1f}%",
    percentage=current_data["cpu_percentage"],
    subtitle=f"{system_info['logical_cpu_cores']} logical cores",
    line_color="#0D9488",
)

memory_card = ResourceCard(
    "Memory",
    f"{current_data['ram_percentage']:.1f}%",
    percentage=current_data["ram_percentage"],
    subtitle=(
        f"{current_data['ram_used_GiB']:.1f} / "
        f"{system_info['total_ram_GiB']:.1f} GiB used"
    ),
    line_color="#0D9488",
)

disk_percentage = current_data["disk_used_percentage"]

disk_card = ResourceCard(
    "Disk Usage",
    f"{disk_percentage:.1f}%" if disk_percentage is not None else "N/A",
    percentage=disk_percentage if disk_percentage is not None else 0,
    subtitle="Storage usage | Read/write activity",
    line_color="#0D9488",
    fixed_plot_scale=False,
)

network_card = ResourceCard(
    "Network",
    "0.00 MB/s",
    subtitle="Download: 0.00 | Upload: 0.00 MB/s",
    line_color="#0D9488",
    fixed_plot_scale=False,
)


# -------------------- CARD GRID --------------------

cards_widget = QWidget()
cards_layout = QGridLayout(cards_widget)
cards_layout.setContentsMargins(0, 0, 0, 0)
cards_layout.setHorizontalSpacing(16)
cards_layout.setVerticalSpacing(16)

cards_layout.addWidget(cpu_card, 0, 0)
cards_layout.addWidget(memory_card, 0, 1)
cards_layout.addWidget(disk_card, 1, 0)
cards_layout.addWidget(network_card, 1, 1)

cards_layout.setColumnStretch(0, 1)
cards_layout.setColumnStretch(1, 1)

main_layout.addWidget(cards_widget)


# -------------------- SYSTEM STATUS --------------------

status_panel = QFrame()
status_panel.setObjectName("statusPanel")
status_panel.setMinimumHeight(80)

status_layout = QVBoxLayout(status_panel)
status_layout.setContentsMargins(18, 16, 18, 16)
status_layout.setSpacing(8)

os = QLabel("Operating System : ")
os.setStyleSheet("""
    color: #064E3B;
    font-size: 16px;
    font-weight: bold;
    background: transparent;
    border: none;
""")

os_info = QLabel(f"Windows {platform.release()}")
os_info.setStyleSheet("""
    color: #64748B;
    font-size: 13px;
    background: transparent;
    border: none;
""")

status_row = QHBoxLayout()
status_row.setSpacing(12)

status_row.addWidget(os)
status_row.addWidget(os_info)
status_row.addStretch()

status_layout.addLayout(status_row)

status_panel.setStyleSheet("""
    QFrame#statusPanel {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
    }
""")

main_layout.addWidget(status_panel)

# -------------------- FOOTER --------------------

footer = QFrame()
footer.setObjectName("footer")

footer_layout = QVBoxLayout(footer)
footer_layout.setContentsMargins(4, 14, 4, 8)
footer_layout.setSpacing(4)

footer_title = QLabel("System Resource Monitor")
footer_title.setStyleSheet("""
    color: #064E3B;
    font-size: 14px;
    font-weight: bold;
    background: transparent;
    border: none;
""")

footer_description = QLabel(
    "Real-time system performance monitoring"
)
footer_description.setStyleSheet("""
    color: #64748B;
    font-size: 12px;
    background: transparent;
    border: none;
""")

footer_credit = QLabel("Developed by : Tanmay Kukreja")
footer_credit.setStyleSheet("""
    color: #059669;
    font-size: 11px;
    background: transparent;
    border: none;
""")

footer_layout.addWidget(footer_title)
footer_layout.addWidget(footer_description)
footer_layout.addWidget(footer_credit)

footer.setStyleSheet("""
    QFrame#footer {
        background: transparent;
        border-top: 1px solid #D1FAE5;
    }
""")

main_layout.addWidget(footer)


# -------------------- RATE CALCULATION --------------------

def calculate_rate(current, previous, elapsed_seconds):
    """Return a non-negative rate in MiB/s."""
    if current is None or previous is None or elapsed_seconds <= 0:
        return 0.0

    difference = max(0, current - previous)
    return difference / elapsed_seconds / (1024 ** 2)


previous_counters = {
    "disk_read_bytes": current_data["disk_read_bytes"],
    "disk_write_bytes": current_data["disk_write_bytes"],
    "network_bytes_sent": current_data["network_bytes_sent"],
    "network_bytes_received": current_data["network_bytes_received"],
}


# Populate the percentage graphs with their initial readings.
cpu_card.update_plot(current_data["cpu_percentage"])
memory_card.update_plot(current_data["ram_percentage"])


# -------------------- UPDATE ALL TELEMETRY --------------------

def update_system_data():
    global previous_sample_time, previous_counters

    data = recurring_sys_data()

    now = time.monotonic()
    elapsed = now - previous_sample_time
    previous_sample_time = now

    # CPU
    cpu = data["cpu_percentage"]

    cpu_card.update_data(
        f"{cpu:.1f}%",
        percentage=cpu,
    )
    cpu_card.update_plot(cpu)

    # Memory
    ram = data["ram_percentage"]

    memory_card.update_data(
        f"{ram:.1f}%",
        percentage=ram,
        subtitle=(
            f"{data['ram_used_GiB']:.1f} / "
            f"{system_info['total_ram_GiB']:.1f} GiB used"
        ),
    )
    memory_card.update_plot(ram)

    # Disk-space utilization plus disk I/O rate
    disk_percent = data["disk_used_percentage"]

    disk_read_rate = calculate_rate(
        data["disk_read_bytes"],
        previous_counters["disk_read_bytes"],
        elapsed,
    )
    disk_write_rate = calculate_rate(
        data["disk_write_bytes"],
        previous_counters["disk_write_bytes"],
        elapsed,
    )

    if disk_percent is not None:
        disk_card.update_data(
            f"{disk_percent:.1f}%",
            percentage=disk_percent,
            subtitle=(
                f"Read {disk_read_rate:.2f} | "
                f"Write {disk_write_rate:.2f} MiB/s"
            ),
        )
    else:
        disk_card.update_data(
            "N/A",
            subtitle=(
                f"Read {disk_read_rate:.2f} | "
                f"Write {disk_write_rate:.2f} MiB/s"
            ),
        )

    disk_card.update_plot(disk_read_rate + disk_write_rate)

    # Network upload/download speeds
    upload_rate = calculate_rate(
        data["network_bytes_sent"],
        previous_counters["network_bytes_sent"],
        elapsed,
    )
    download_rate = calculate_rate(
        data["network_bytes_received"],
        previous_counters["network_bytes_received"],
        elapsed,
    )

    total_network_rate = upload_rate + download_rate

    network_card.update_data(
        f"{total_network_rate:.2f} MiB/s",
        subtitle=(
            f"Download: {download_rate:.2f} | "
            f"Upload: {upload_rate:.2f} MiB/s"
        ),
    )
    network_card.update_plot(total_network_rate)

    # Save counters for the next rate calculation.
    previous_counters = {
        "disk_read_bytes": data["disk_read_bytes"],
        "disk_write_bytes": data["disk_write_bytes"],
        "network_bytes_sent": data["network_bytes_sent"],
        "network_bytes_received": data["network_bytes_received"],
    }


# -------------------- AUTOMATIC REFRESH --------------------

timer = QTimer()
timer.timeout.connect(update_system_data)
timer.start(2000)

window.show()
sys.exit(app.exec())
