import ctypes
import json
import os
import platform


def get_windows_info():
    import winreg

    info = {}

    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
    info["cpu"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()

    ram_kb = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(ram_kb))
    info["ram_gb"] = round(ram_kb.value / 1024 ** 2, 2)

    gpu_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    info["gpu"] = []
    for i in range(10):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, gpu_path + "\\" + str(i).zfill(4))
            info["gpu"].append(winreg.QueryValueEx(key, "DriverDesc")[0])
        except OSError:
            pass

    return info


def get_linux_info():
    info = {}

    info["cpu"] = "Unknown"
    for line in open("/proc/cpuinfo"):
        if line.startswith("model name"):
            info["cpu"] = line.split(":")[1].strip()
            break

    for line in open("/proc/meminfo"):
        if line.startswith("MemTotal"):
            info["ram_gb"] = round(int(line.split()[1]) / 1024 ** 2, 2)
            break

    return info


def get_mac_info():
    libc = ctypes.CDLL(None)
    info = {}

    buf = ctypes.create_string_buffer(256)
    size = ctypes.c_size_t(256)
    libc.sysctlbyname(b"machdep.cpu.brand_string", buf, ctypes.byref(size), None, 0)
    info["cpu"] = buf.value.decode()

    ram_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    info["ram_gb"] = round(ram_bytes / 1024 ** 3, 2)

    return info


def collect_info():
    system = platform.system()

    if system == "Windows":
        info = get_windows_info()
    elif system == "Linux":
        info = get_linux_info()
    elif system == "Darwin":
        info = get_mac_info()
    else:
        info = {}

    info["os"] = system + " " + platform.release()
    info["architecture"] = platform.machine()
    info["logical_cores"] = os.cpu_count()
    return info


def save_to_file(info, file_name):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(info, file, indent=4, ensure_ascii=False)

data = collect_info()
save_to_file(data, "pc_specs.json")
print(json.dumps(data, indent=4, ensure_ascii=False))