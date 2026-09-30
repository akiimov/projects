import ctypes
import ctypes.util
import json
import os
import platform

UNKNOWN = "Unknown"


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as file:
            return file.read().strip()
    except OSError:
        return ""


def os_info():
    return {
        "name": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "computer_name": platform.node(),
    }


def python_info():
    return {
        "platform": platform.platform(),
        "version": platform.python_version(),
    }

def windows_ram_gb():
    ram_kb = ctypes.c_ulonglong(0)
    if ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(ram_kb)):
        return round(ram_kb.value / 1024 ** 2, 2)
    return 0

def windows_physical_cores():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    relation_processor_core = 0

    length = ctypes.c_ulong(0)
    kernel32.GetLogicalProcessorInformationEx(relation_processor_core, None, ctypes.byref(length))
    if length.value == 0:
        return UNKNOWN

    buffer = ctypes.create_string_buffer(length.value)
    if not kernel32.GetLogicalProcessorInformationEx(
            relation_processor_core, buffer, ctypes.byref(length)):
        return UNKNOWN

    data = buffer.raw
    offset = 0
    cores = 0
    while offset + 8 <= length.value:
        relationship = int.from_bytes(data[offset:offset + 4], "little")
        size = int.from_bytes(data[offset + 4:offset + 8], "little")
        if size == 0:
            break
        if relationship == relation_processor_core:
            cores += 1
        offset += size
    return cores or UNKNOWN

def windows_cpu_name():
    import winreg
    path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except OSError:
        return UNKNOWN

def windows_gpu_names():
    import winreg
    path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    names = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as class_key:
            index = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(class_key, index)
                except OSError:
                    break
                index += 1
                try:
                    with winreg.OpenKey(class_key, sub_name) as adapter_key:
                        name = winreg.QueryValueEx(adapter_key, "DriverDesc")[0]
                        if name not in names:
                            names.append(name)
                except OSError:
                    continue
    except OSError:
        pass
    return names

def windows_hardware():
    return {
        "cpu": {
            "model": windows_cpu_name(),
            "physical_cores": windows_physical_cores(),
            "logical_cores": os.cpu_count() or UNKNOWN,
        },
        "ram_gb": windows_ram_gb(),
        "gpus": windows_gpu_names() or [UNKNOWN],
    }

def load_libc():
    return ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


def sysctl_bytes(libc, name):
    size = ctypes.c_size_t(0)
    if libc.sysctlbyname(name.encode(), None, ctypes.byref(size), None, 0) != 0:
        return b""
    buffer = ctypes.create_string_buffer(size.value)
    if libc.sysctlbyname(name.encode(), buffer, ctypes.byref(size), None, 0) != 0:
        return b""
    return buffer.raw[:size.value]

def sysctl_text(libc, name):
    return sysctl_bytes(libc, name).split(b"\0", 1)[0].decode(errors="replace").strip()

def sysctl_number(libc, name):
    raw = sysctl_bytes(libc, name)
    return int.from_bytes(raw, "little") if raw else None

def mac_hardware():
    libc = load_libc()

    cpu_model = sysctl_text(libc, "machdep.cpu.brand_string") or UNKNOWN
    physical = sysctl_number(libc, "hw.physicalcpu")
    logical = sysctl_number(libc, "hw.logicalcpu")
    ram_bytes = sysctl_number(libc, "hw.memsize")

    if platform.machine() == "arm64":
        gpus = [f"Integrated (part of {cpu_model})"]
    else:
        gpus = [UNKNOWN]

    return {
        "cpu": {
            "model": cpu_model,
            "physical_cores": physical or UNKNOWN,
            "logical_cores": logical or UNKNOWN,
        },
        "ram_gb": round(ram_bytes / 1024 ** 3, 2) if ram_bytes else 0,
        "gpus": gpus,
    }

def linux_cpu_name():
    for line in read_text("/proc/cpuinfo").splitlines():
        key, _, value = line.partition(":")
        if key.strip() in ("model name", "Hardware", "Model") and value.strip():
            return value.strip()
    return read_text("/proc/device-tree/model").strip("\0") or UNKNOWN

def linux_physical_cores():
    cores = set()
    cpu_root = "/sys/devices/system/cpu"
    try:
        entries = os.listdir(cpu_root)
    except OSError:
        return UNKNOWN
    for entry in entries:
        if not (entry.startswith("cpu") and entry[3:].isdigit()):
            continue
        topology = f"{cpu_root}/{entry}/topology"
        package_id = read_text(f"{topology}/physical_package_id")
        core_id = read_text(f"{topology}/core_id")
        if core_id:
            cores.add((package_id, core_id))
    return len(cores) or UNKNOWN

def linux_ram_gb():
    for line in read_text("/proc/meminfo").splitlines():
        if line.startswith("MemTotal:"):
            return round(int(line.split()[1]) / 1024 / 1024, 2)
    return 0

def find_in_pci_ids(vendor_id, device_id):
    database = ""
    for path in ("/usr/share/hwdata/pci.ids", "/usr/share/misc/pci.ids", "/usr/share/pci.ids"):
        database = read_text(path)
        if database:
            break
    vendor_name = device_name = None
    for line in database.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        if not line.startswith("\t"):
            if vendor_name is not None:
                break
            if line.startswith(vendor_id):
                vendor_name = line[len(vendor_id):].strip()
        elif vendor_name is not None and line.startswith("\t") and not line.startswith("\t\t"):
            if line.strip().startswith(device_id):
                device_name = line.strip()[len(device_id):].strip()
                break
    return vendor_name, device_name

def linux_gpu_names():
    pci_root = "/sys/bus/pci/devices"
    names = []
    try:
        devices = sorted(os.listdir(pci_root))
    except OSError:
        return names
    for device in devices:
        if not read_text(f"{pci_root}/{device}/class").startswith("0x03"):
            continue
        vendor_id = read_text(f"{pci_root}/{device}/vendor").removeprefix("0x")
        device_id = read_text(f"{pci_root}/{device}/device").removeprefix("0x")
        vendor_name, device_name = find_in_pci_ids(vendor_id, device_id)
        if vendor_name and device_name:
            names.append(f"{vendor_name} {device_name}")
        else:
            names.append(f"PCI ID {vendor_id}:{device_id}")
    return names

def linux_hardware():
    return {
        "cpu": {
            "model": linux_cpu_name(),
            "physical_cores": linux_physical_cores(),
            "logical_cores": os.cpu_count() or UNKNOWN,
        },
        "ram_gb": linux_ram_gb(),
        "gpus": linux_gpu_names() or [UNKNOWN],
    }

def get_hardware_info():
    system = platform.system()
    if system == "Windows":
        return windows_hardware()
    if system == "Darwin":
        return mac_hardware()
    if system == "Linux":
        return linux_hardware()
    return "Операционная система не поддерживается"

def collect_info():
    return {
        "os": os_info(),
        "python": python_info(),
        "hardware": get_hardware_info(),
    }

if __name__ == "__main__":
    info = collect_info()
    file_name = "pc_specs.json"

    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(info, file, indent=4, ensure_ascii=False)

    print(f"Данные сохранены в файл: {os.path.abspath(file_name)}")