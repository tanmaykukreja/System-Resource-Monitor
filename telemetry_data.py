import platform
import sys
import PySide6
import os
import psutil
from datetime import datetime


def static_data():
    frequency = psutil.cpu_freq()
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "physical_cpu_cores": psutil.cpu_count(logical=False),
        "logical_cpu_cores": psutil.cpu_count(logical=True),
        "max_cpu_frequency_GHz": (
            round(frequency.max / 1000, 3)
            if frequency and frequency.max else None
        ),
        "total_ram_GiB": round(ram.total / (1024 ** 3), 4),
        "total_swap_GiB": round(swap.total / (1024 ** 3), 4),
        "os": platform.system(),
        "os_version" : platform.version(),
        "architecture":platform.machine(),
    }


def initialize_cpu_sampling():
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)


def recurring_sys_data():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cpu_percent = psutil.cpu_percent(interval=None)
    per_cpu_percent = psutil.cpu_percent(interval=None, percpu=True)

    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    disk_io = psutil.disk_io_counters()
    network_io = psutil.net_io_counters()

    # Use the Windows system drive when available.
    # On other systems, use the root filesystem.
    drive = os.environ.get("SystemDrive", "C:") + os.sep
    if os.name != "nt":
        drive = "/"

    try:
        disk = psutil.disk_usage(drive)
    except (OSError, PermissionError):
        disk = None

    return {
        "timestamp": timestamp,

        "cpu_percentage": cpu_percent,
        "cpu_percentage_per_logical_cpu": per_cpu_percent,

        "ram_percentage": ram.percent,
        "ram_used_GiB": round(ram.used / (1024 ** 3), 4),
        "ram_available_GiB": round(ram.available / (1024 ** 3), 4),

        "swap_percentage": swap.percent,
        "swap_used_GiB": round(swap.used / (1024 ** 3), 4),

        "disk_used_percentage": disk.percent if disk else None,
        "disk_used_GiB": (
            round(disk.used / (1024 ** 3), 2) if disk else None
        ),
        "disk_total_GiB": (
            round(disk.total / (1024 ** 3), 2) if disk else None
        ),
        "disk_free_GiB": (
            round(disk.free / (1024 ** 3), 2) if disk else None
        ),

        "disk_read_bytes": (
            disk_io.read_bytes if disk_io is not None else None
        ),
        "disk_write_bytes": (
            disk_io.write_bytes if disk_io is not None else None
        ),

        "network_bytes_sent": (
            network_io.bytes_sent if network_io is not None else None
        ),
        "network_bytes_received": (
            network_io.bytes_recv if network_io is not None else None
        ),
        "network_packets_sent": (
            network_io.packets_sent if network_io is not None else None
        ),
        "network_packets_received": (
            network_io.packets_recv if network_io is not None else None
        ),

        "process_count": len(psutil.pids()),
    }

