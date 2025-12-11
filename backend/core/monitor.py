import psutil
import wmi
import GPUtil
import platform
import time

# Initialize WMI
try:
    w = wmi.WMI()
except:
    w = None

def get_static_info():
    """Fetches static system details (run once on startup)."""
    try:
        # Fetch detailed system info using WMI
        cs = w.Win32_ComputerSystem()[0]
        os_info = w.Win32_OperatingSystem()[0]
        proc = w.Win32_Processor()[0]
        
        info = {
            "node": platform.node(), # Computer Name
            "os": f"{platform.system()} {platform.release()}",
            "manufacturer": cs.Manufacturer,
            "model": cs.Model,
            "processor": proc.Name,
            "ram_total": f"{round(int(cs.TotalPhysicalMemory) / (1024**3), 2)} GB"
        }
    except Exception as e:
        # Fallback if WMI fails
        info = {
            "node": platform.node(),
            "os": platform.platform(),
            "manufacturer": "Unknown",
            "model": "Generic PC",
            "processor": platform.processor(),
            "ram_total": "Unknown"
        }
    return info

def get_system_metrics():
    """Fetches real-time metrics."""
    
    # 1. CPU Usage
    cpu_usage = psutil.cpu_percent(interval=None)
    
    # 2. Temperature (Improved Logic for Windows)
    cpu_temp = 0
    try:
        # Method A: psutil (Standard)
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            cpu_temp = temps['coretemp'][0].current
        # Method B: WMI (Windows specific fallback)
        elif w:
            thermal = w.MSAcpi_ThermalZoneTemperature()
            if thermal:
                # WMI returns temp in Kelvin * 10, convert to Celsius
                kelvin = thermal[0].CurrentTemperature
                cpu_temp = (kelvin - 2732) / 10.0
    except:
        pass # Keep 0 if strictly unreadable (Admin rights often needed)

    # 3. GPU (Handle Missing GPU)
    gpu_data = None
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_data = {
                "name": gpus[0].name,
                "usage": gpus[0].load * 100,
                "temp": gpus[0].temperature
            }
    except:
        gpu_data = None # Explicitly set None if no GPU found

    # 4. Kernel Stats
    cpu_stats = psutil.cpu_stats()
    
    metrics = {
        "timestamp": time.time(),
        "cpu": {
            "usage_percent": cpu_usage,
            "temperature": cpu_temp
        },
        "gpu": gpu_data, # Will be None if no GPU
        "kernel": {
            "context_switches": cpu_stats.ctx_switches,
            "interrupts": cpu_stats.interrupts,
            "dpcs_stalls": cpu_stats.soft_interrupts,
            "processes": len(psutil.pids())
        }
    }
    return metrics