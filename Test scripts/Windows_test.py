import psutil
import os
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def get_cpu_info():
    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "total_cores": psutil.cpu_count(logical=True),
        "max_frequency": psutil.cpu_freq().max,
        "min_frequency": psutil.cpu_freq().min,
        "current_frequency": psutil.cpu_freq().current,
        "usage": psutil.cpu_percent(interval=1)
    }

def get_memory_info():
    virtual_memory = psutil.virtual_memory()
    return {
        "total": virtual_memory.total,
        "available": virtual_memory.available,
        "used": virtual_memory.used,
        "percent": virtual_memory.percent
    }

def get_disk_info():
    disk_usage = psutil.disk_usage('/')
    return {
        "total": disk_usage.total,
        "used": disk_usage.used,
        "free": disk_usage.free,
        "percent": disk_usage.percent
    }

def get_system_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume.GetMasterVolumeLevelScalar()

def set_system_volume(volume_level):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(volume_level, None)

def shutdown():
    os.system("shutdown /s /t 1")

def restart():
    os.system("shutdown /r /t 1")

def kill_process(process_name):
    os.system("taskkill /f /im " + process_name)

if __name__ == "__main__":
    cpu_info = get_cpu_info()
    memory_info = get_memory_info()
    disk_info = get_disk_info()
    system_volume = get_system_volume()
    print(f"CPU Usage: {cpu_info['usage']}%")
    print(f"Memory Usage: {memory_info['percent']}%")
    print(f"Disk Usage: {disk_info['percent']}%")
    print(f"System Volume: {system_volume * 100:.2f}%")
    #set_system_volume(0.5)
    #print('Rebooting in 5 seconds...')
    #import time
    #time.sleep(5)
    #restart()
    #kill_process("chrome.exe")

